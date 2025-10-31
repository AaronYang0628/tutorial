import os
from flask_cors import CORS
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_restx import Api, Resource, fields
from pymilvus import MilvusClient
from openai import OpenAI
from imgSearch.feature_extractor import FeatureExtractor
from imgSearch.predicator import get_similar_image_paths
from utils.env_utils import load_env_config
from ragQA.qa_rag import answer_question
from ragQA.update_rag import update_rag_collection
from utils.logger_util import setup_logging

logger = setup_logging()


app = Flask(__name__)

extractor = FeatureExtractor("resnet34")

origin = os.environ.get("ALLOW_HOST", "http://127.0.0.1:30500")

# 启用CORS支持，允许所有来源的跨域请求
CORS(app, resources={
    r"/api/*": {
        "origins": [origin],
        "allow_headers": ["Content-Type"],
        "methods": ["GET", "POST", "OPTIONS"]
    },
    r"/img": {
        "origins": [origin],
        "allow_headers": ["Content-Type"],
        "methods": ["GET", "POST", "OPTIONS"]
    },
    r"/uploads/*": {
        "origins": [origin],
        "allow_headers": ["Content-Type"],
        "methods": ["GET"]
    }
})

# 配置Swagger文档
api = Api(
    app,
    version='1.0',
    title='RAG 问答系统 API',
    description='基于Milvus向量数据库的问答系统接口文档',
    prefix='/api',
    doc='/swagger/'  # Swagger UI文档地址
)

# 定义命名空间
ns_chat = api.namespace('chat', description='问答相关接口')
ns_upgrade = api.namespace('upgrade', description='数据库更新相关接口')
ns_health = api.namespace('health', description='健康检查接口')
ns_file = api.namespace('file', description='文件处理相关接口')
ns_img = api.namespace('img', description='图像搜索相关接口')

# 定义请求模型
chat_model = api.model('ChatRequest', {
    'question': fields.String(required=True, description='用户问题')
})

upgrade_model = api.model('UpgradeRequest', {
    'mode': fields.String(required=False, description='操作模式: create 或 upgrade', default='upgrade'),
    'doc_path': fields.String(required=False, description='文档路径')
})

img_search_model = api.model('ImageSearchRequest', {
    'image_path': fields.String(required=True, description='图像文件路径'),
    'top_k': fields.Integer(required=False, description='返回结果数量', default=10)
})

file_upload_model = ns_file.parser()
file_upload_model.add_argument('file', type='file', location='files', required=True, help='要上传的文件')


# 加载配置
def get_config():
    return {
        "milvus_uri": os.environ.get("MILVUS_URI", origin),
        "token": os.environ.get("MILVUS_TOKEN", ""),
        "collection_name": os.environ.get("QA_COLLECTION_NAME", "default_collection"),
        "embedding_dim": int(os.environ.get("EMBEDDING_DIM", "1024")),
        "embedding_model": os.environ.get("EMBEDDING_MODEL", ""),
        "tongyi_api_key": os.environ.get("TONGYI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        "model_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "llm_model": os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
        "grab_top_n_res": int(os.environ.get("GRABE_TOP_N_RES", "5")),
        "ext_doc_path": os.environ.get("EXT_DOC_PATH", "milvus_docs/en/faq/*.md")
    }

# 定义上传文件夹和允许的文件扩展名
UPLOAD_FOLDER = 'uploads'
PRESET_FOLDER = 'preset'
ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_FILE_EXTENSIONS = {'md', 'pdf','txt', 'docx'}

# 初始化客户端
def init_clients(config):
    openai_client = OpenAI(
        api_key=config["tongyi_api_key"],
        base_url=config["model_base_url"],
    )
    
    milvus_client = MilvusClient(uri=config["milvus_uri"], token=config["token"])
    return openai_client, milvus_client

# 全局客户端实例
config = get_config()
openai_client, milvus_client = init_clients(config)

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'docs'), exist_ok=True)
preset_path = os.path.join(UPLOAD_FOLDER, PRESET_FOLDER)
os.makedirs(preset_path, exist_ok=True)
if not os.listdir(preset_path): 
    import requests
    import zipfile
    logger.info(f"Preset Image folder is empty, downloading preset images to {preset_path}")
    # 下载预设图片数据
    zip_url = "https://github.com/milvus-io/pymilvus-assets/releases/download/imagedata/reverse_image_search.zip"
    zip_path = os.path.join(preset_path, "reverse_image_search.zip")
    
    try:
        response = requests.get(zip_url)
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # 解压到preset目录下的images文件夹
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(preset_path, "images"))
        
        logger.info("Preset Image zip have been downloaded and extracted.")
        # 删除下载的zip文件
        os.remove(zip_path)
    except Exception as e:
        logger.error(f"Failed to download or extract preset images: {e}")
    
    

# 设置应用配置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """检查文件是否有有效的扩展名"""
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

def allowed_img(filename):
    """检查图片文件是否有有效的扩展名"""
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXTENSIONS
        
# 添加静态文件路由，使HTML文件可以被访问
@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)


@ns_file.route('', methods=['POST'])
class UploadFileResource(Resource):
    @ns_file.expect(file_upload_model)
    @api.response(200, '上传成功')
    @api.response(400, '参数错误')
    def post(self):
        # 检查请求中是否包含文件
        if 'file' not in request.files:
            return {'error': 'No file part'}, 400
        
        file = request.files['file']
        
        if file.filename == '':
            return {'error': 'No selected file'}, 400
        
        upload_folder = None
        if allowed_img(file.filename):
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
        elif allowed_file(file.filename):
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'docs')
        else:
            return {'error': 'File type not allowed'}, 400

        # 确保上传文件夹存在
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        # 使用secure_filename确保文件名安全，并生成唯一文件名避免冲突
        safe_filename = secure_filename(file.filename)
        ext = safe_filename.rsplit('.', 1)[1].lower() if '.' in safe_filename else ''
        unique_filename = f"{os.urandom(8).hex()}.{ext}" if ext else os.urandom(8).hex()
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # 构建完整的文件URL路径（使用正斜杠，适用于所有平台）
        file_url = f"{request.host_url}{upload_folder.replace(os.sep, '/')}/{unique_filename}"
        
        return {'path': file_url}


@ns_img.route('/search', methods=['POST'])
class SearchImageResource(Resource):
    @ns_img.expect(img_search_model)
    @api.response(200, '搜索成功')
    @api.response(400, '参数错误')
    @api.response(404, '图片不存在')
    @api.response(500, '服务器内部错误')
    def post(self): 
        try:
            # 获取请求参数
            data = request.json or {}
            image_url_path = data.get('image_path')
            top_k = int(data.get('top_k', 10))
            
            # 从URL路径提取文件名
            filename = os.path.basename(image_url_path)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename)
                
            if not os.path.exists(image_path):
                return jsonify({"error": f"Image not found at path: {image_path}"}), 404
            
            # 初始化图像搜索所需的组件
            extractor = FeatureExtractor("resnet34")
            collection_name = os.environ.get("IMAGE_COLLECTION_NAME", "image_embeddings")
            

            # 使用抽象函数获取相似图像路径
            similar_images = get_similar_image_paths(
                query_image_path=image_path,
                milvus_client=milvus_client,
                extractor=extractor,
                collection_name=collection_name,
                top_k=top_k
            )
            
            # 返回结果
            if similar_images:
                return jsonify({
                    "status": "success",
                    "message": f"Found {len(similar_images)} similar images",
                    "data": similar_images
                })
            else:
                return jsonify({
                    "status": "success",
                    "message": "No similar images found",
                    "data": []
                })
                
        except Exception as e:
            app.logger.error(f"Error in image search: {str(e)}")
            return jsonify({"error": str(e)}), 500


@ns_chat.route('')
class ChatResource(Resource):
    @api.expect(chat_model)
    @api.response(200, '成功')
    @api.response(400, '参数错误')
    @api.response(404, '集合不存在')
    @api.response(500, '服务器内部错误')
    def post(self):
        try:
            data = request.json
            if not data or "question" not in data:
                return jsonify({"error": "Missing 'question' field in request"}), 400
            
            question = data["question"]
            
            # 检查集合是否存在
            if not milvus_client.has_collection(config["collection_name"]):
                return jsonify({"error": f"Collection {config['collection_name']} not found"}), 404
            
            # 调用共享的 answer_question 函数获取回答
            result = answer_question(
                question=question,
                milvus_client=milvus_client,
                openai_client=openai_client,
                collection_name=config["collection_name"],
                embedding_model=config["embedding_model"],
                grab_top_n_res=config["grab_top_n_res"],
                llm_model=config["llm_model"]
            )
            
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Error processing chat request: {str(e)}")
            return jsonify({"error": str(e)}), 500

@ns_upgrade.route('')
class UpgradeResource(Resource):
    @api.expect(upgrade_model)
    @api.response(200, '成功')
    @api.response(400, '参数错误')
    @api.response(404, '集合不存在')
    @api.response(500, '服务器内部错误')
    def post(self):
        try:
            # 重新加载配置以获取最新环境变量
            global config, openai_client, milvus_client
            data = request.json or {}
            mode = data.get("mode", os.environ.get("MODE", "upgrade"))
            doc_path = data.get("doc_path")
            if not doc_path:
                return jsonify({"error": "Missing 'doc_path' field in request"}), 400
            
            filename = os.path.basename(doc_path)
            abs_doc_path = os.path.join(app.config['UPLOAD_FOLDER'], 'docs', filename)
                
            if not os.path.exists(abs_doc_path):
                return jsonify({"error": f"Document not found at path: {abs_doc_path}"}), 404
            # 使用抽象的update_rag_collection函数更新向量库
            update_result = update_rag_collection(
                mode=mode,
                doc_path=abs_doc_path,
                milvus_client=milvus_client,
                openai_client=openai_client,
                collection_name=config["collection_name"],
                embedding_dim=config["embedding_dim"],
                embedding_model=config["embedding_model"]
            )
            
            # 构造返回结果
            result = {
                "status": "success",
                "message": update_result["message"],
                "flush_time": update_result.get("flush_time")
            }
            
            return jsonify(result)
            
        except ValueError as e:
            error_msg = str(e)
            if "Collection" in error_msg and "does not exist" in error_msg:
                return jsonify({"error": error_msg}), 404
            elif "Unknown mode" in error_msg:
                return jsonify({"error": error_msg}), 400
            else:
                app.logger.error(f"Value error during update: {error_msg}")
                raise
        except Exception as e:
            app.logger.error(f"Error processing update request: {str(e)}")
            return jsonify({"error": str(e)}), 500

@ns_health.route('')
class HealthResource(Resource):
    @api.response(200, '服务健康')
    @api.response(503, '服务不健康')
    def get(self):
        try:
            # 检查Milvus连接
            has_collection = milvus_client.has_collection(config["collection_name"])
            return jsonify({
                "status": "healthy",
                "milvus_connected": True,
                "collection_exists": has_collection,
                "collection_name": config["collection_name"]
            })
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 503

if __name__ == '__main__':
    load_env_config()
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 30500))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)


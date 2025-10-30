# from dotenv import load_dotenv

# load_dotenv()

import os
import time
from flask_cors import CORS
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_restx import Api, Resource, fields
from pymilvus import MilvusClient
from openai import OpenAI
from util import embedding_text, read_markdown
from tqdm import tqdm
from imgSearch.feature_extractor import FeatureExtractor

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

# 定义请求模型
chat_model = api.model('ChatRequest', {
    'question': fields.String(required=True, description='用户问题')
})

upgrade_model = api.model('UpgradeRequest', {
    'mode': fields.String(required=False, description='操作模式: create 或 append', default='create'),
    'doc_path': fields.String(required=False, description='文档路径')
})

# 加载配置
def get_config():
    return {
        "milvus_uri": os.environ.get("MILVUS_URI", origin),
        "token": os.environ.get("MILVUS_TOKEN", ""),
        "collection_name": os.environ.get("MILVUS_COLLECTION", "default_collection"),
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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 确保上传文件夹存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 设置应用配置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 图片上传接口
@app.route('/img', methods=['POST'])
def upload_image():
    # 检查请求中是否包含文件
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']

    # 检查请求中是否包含文件
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    # 如果用户没有选择文件，浏览器也会提交一个没有文件名的空文件
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 检查文件类型是否允许
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # 确保文件名安全并保存文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # 构建完整的文件URL路径
    file_url = f"{request.host_url}uploads/{filename}"
    
    return jsonify({'path': file_url}), 200

# 提供上传文件的访问路由
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/img/search', methods=['POST'])
def search_similar_images():
    try:
        data = request.json
        image_path = data.get('image_path')
        if not image_path:
            return jsonify({'error': 'No image path provided'}), 400

        # 从URL中提取文件名
        filename = image_path.split('/')[-1]
        
        # 构建服务器上的完整路径
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(full_path):
            return jsonify({'error': 'Image not found'}), 404

        # 提取特征向量
        feature_vector = extractor(full_path)

        # 在Milvus中搜索相似图片
        results = milvus_client.search(
            "image_embeddings",
            data=[feature_vector],
            output_fields=["filename"],
            search_params={"metric_type": "COSINE"},
        )

        # 获取前10个结果的文件路径
        similar_images = []
        if results and len(results) > 0:
            for hit in results[0][:10]:
                src_path = hit["entity"]["filename"]  # 原始文件完整路径
                if os.path.exists(src_path):
                    # 从完整路径中提取文件名
                    filename = os.path.basename(src_path)
                    # 构建目标路径
                    dest_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # 如果目标文件不存在，复制文件
                    if not os.path.exists(dest_path):
                        import shutil
                        shutil.copy2(src_path, dest_path)
                    
                    # 构建完整的URL路径
                    file_url = f"{request.host_url}uploads/{filename}"
                    similar_images.append(file_url)

        return jsonify({
            'fetched_results_from_milvus': results[0][:10],
            'similar_images': similar_images
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


# 添加静态文件路由，使HTML文件可以被访问
@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

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
            
            # 搜索相似文本
            search_res = milvus_client.search(
                collection_name=config["collection_name"],
                data=[
                    embedding_text(openai_client, question, config["embedding_model"])
                ],
                limit=config["grab_top_n_res"],
                search_params={"metric_type": "IP", "params": {}},
                output_fields=["text"],
            )
            
            # 处理搜索结果
            retrieved_lines_with_distances = [
                (res["entity"]["text"], res["distance"]) for res in search_res[0]
            ]
            
            context = "\n".join(
                [line_with_distance[0] for line_with_distance in retrieved_lines_with_distances]
            )
            
            # 构建提示词
            SYSTEM_PROMPT = """
            Human: You are an AI assistant. You are able to find answers to the questions from the contextual passage snippets provided.
            """
            USER_PROMPT = f"""
            Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.
            <context>
            {context}
            </context>
            <question>
            {question}
            </question>
            """
            
            # 获取LLM回答
            response = openai_client.chat.completions.create(
                model=config["llm_model"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT},
                ],
            )
            
            return jsonify({
                "response": response.choices[0].message.content,
                "sources": retrieved_lines_with_distances
            })
            
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
            mode = data.get("mode", os.environ.get("MODE", "create"))
            
            # 配置已在函数开头更新
            config = get_config()
            openai_client, milvus_client = init_clients(config)
            
            doc_path = data.get("doc_path", config["ext_doc_path"])
            
            result = {"status": "success", "message": ""}
            
            if mode == "create":
                cooked_data = []
                
                # 读取文档
                raw_text_lines = read_markdown(doc_path)
                
                # 如果集合已存在则删除
                if milvus_client.has_collection(config["collection_name"]):
                    milvus_client.drop_collection(config["collection_name"])
                    result["message"] += f"Dropped existing collection {config['collection_name']}. "
                
                # 创建新集合
                milvus_client.create_collection(
                    collection_name=config["collection_name"],
                    dimension=config["embedding_dim"],
                    metric_type="IP",
                    consistency_level="Bounded",
                )
                
                result["message"] += f"Created collection {config['collection_name']}. "
                
                # 生成嵌入并插入数据
                for i, line in enumerate(tqdm(raw_text_lines, desc="Creating embeddings")):
                    cooked_data.append({
                        "id": i, 
                        "vector": embedding_text(openai_client, line, config["embedding_model"]), 
                        "text": line
                    })
                
                milvus_client.insert(collection_name=config["collection_name"], data=cooked_data)
                result["message"] += f"Inserted {len(cooked_data)} documents."
            
            elif mode == "append":
                if milvus_client.has_collection(config["collection_name"]):
                    cooked_data = []
                    
                    # 读取文档
                    raw_text_lines = read_markdown(doc_path)
                    
                    # 获取当前最大ID
                    max_id = 0
                    try:
                        # 尝试获取现有文档的最大ID
                        query_res = milvus_client.query(
                            collection_name=config["collection_name"],
                            filter="",
                            output_fields=["id"],
                            limit=1,
                            offset=0,
                            consistency_level="Strong"
                        )
                        if query_res:
                            max_id = max([res["id"] for res in query_res])
                    except Exception as e:
                        app.logger.warning(f"Failed to get max ID, starting from 0: {str(e)}")
                    
                    # 生成嵌入并插入新数据
                    for i, line in enumerate(tqdm(raw_text_lines, desc="Creating embeddings")):
                        cooked_data.append({
                            "id": max_id + i + 1,  # 避免ID冲突
                            "vector": embedding_text(openai_client, line, config["embedding_model"]), 
                            "text": line
                        })
                    
                    milvus_client.insert(collection_name=config["collection_name"], data=cooked_data)
                    result["message"] += f"Appended {len(cooked_data)} documents."
                else:
                    return jsonify({"error": f"Collection {config['collection_name']} does not exist"}), 404
            
            else:
                return jsonify({"error": f"Unknown mode {mode}"}), 400
            
            # 刷新数据
            start_flush = time.time()
            milvus_client.flush(config["collection_name"])
            end_flush = time.time()
            result["flush_time"] = round(end_flush - start_flush, 4)
            result["message"] += f" Flush completed in {result['flush_time']} seconds."
            
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Error processing upgrade request: {str(e)}")
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
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 30500))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
import os
import time
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_restx import Api, Resource, fields
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加agent目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import HelloAgentsLLM
from utils.tools import ToolExecutor, search
from PlanandSolve.AgentTest import PlanAndSolveAgent
from ReAct.AgentTest import ReActAgent
from Reflection.AgentTest import ReflectionAgent

app = Flask(__name__)

# 配置CORS
origin = os.environ.get("ALLOW_HOST", "http://127.0.0.1:5000")
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "allow_headers": ["Content-Type"],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})

# 配置Swagger文档
api = Api(
    app,
    version='1.0',
    title='Multi-Agent 系统 API',
    description='支持多种AI Agent的智能对话系统',
    prefix='/api',
    doc='/swagger/'
)

# 定义命名空间
ns_chat = api.namespace('chat', description='多Agent对话接口')
ns_health = api.namespace('health', description='健康检查接口')

# 定义请求模型
chat_model = api.model('ChatRequest', {
    'question': fields.String(required=True, description='用户问题'),
    'agent_type': fields.String(
        required=False, 
        description='Agent类型: plan-solve, react, reflection',
        default='plan-solve'
    )
})

# 全局变量存储Agent实例
llm_client = None
agents = {}

def init_agents():
    """初始化所有Agent"""
    global llm_client, agents
    
    try:
        logger.info("🔧 开始初始化LLM客户端...")
        llm_client = HelloAgentsLLM()
        logger.info(f"✅ LLM客户端初始化成功，模型: {llm_client.model}")
        
        # 初始化Plan-and-Solve Agent
        logger.info("🔧 初始化 Plan-and-Solve Agent...")
        agents['plan-solve'] = PlanAndSolveAgent(llm_client)
        logger.info("✅ Plan-and-Solve Agent 初始化完成")
        
        # 初始化ReAct Agent
        logger.info("🔧 初始化 ReAct Agent...")
        tool_executor = ToolExecutor()
        search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
        tool_executor.registerTool("Search", search_desc, search)
        agents['react'] = ReActAgent(llm_client=llm_client, tool_executor=tool_executor)
        logger.info("✅ ReAct Agent 初始化完成")
        
        # 初始化Reflection Agent
        logger.info("🔧 初始化 Reflection Agent...")
        agents['reflection'] = ReflectionAgent(llm_client, max_iterations=2)
        logger.info("✅ Reflection Agent 初始化完成")
        
        logger.info("=" * 60)
        logger.info("✅ 所有Agent初始化完成")
        logger.info(f"📋 可用Agents: {', '.join(agents.keys())}")
        logger.info("=" * 60)
        return True
    except Exception as e:
        logger.error(f"❌ Agent初始化失败: {e}")
        return False

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@ns_chat.route('')
class ChatResource(Resource):
    @api.expect(chat_model)
    @api.response(200, '成功')
    @api.response(400, '参数错误')
    @api.response(500, '服务器内部错误')
    def post(self):
        """
        与指定的Agent进行对话
        """
        start_time = time.time()
        
        try:
            data = request.json
            if not data or "question" not in data:
                logger.error("请求缺少 'question' 字段")
                return jsonify({"error": "Missing 'question' field in request"}), 400
            
            question = data["question"]
            agent_type = data.get("agent_type", "plan-solve")
            
            logger.info(f"=" * 60)
            logger.info(f"🚀 收到新请求")
            logger.info(f"📝 问题: {question}")
            logger.info(f"🤖 选择Agent: {agent_type}")
            logger.info(f"=" * 60)
            
            # 验证agent类型
            if agent_type not in agents:
                logger.error(f"未知的Agent类型: {agent_type}")
                return jsonify({
                    "error": f"Unknown agent type: {agent_type}",
                    "available_agents": list(agents.keys())
                }), 400
            
            # 根据agent类型调用不同的处理方法
            agent = agents[agent_type]
            logger.info(f"⚙️ 开始执行 {agent_type} Agent...")
            
            # 捕获输出
            import io
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            result = None
            
            agent_start_time = time.time()
            
            try:
                with redirect_stdout(output_buffer):
                    if agent_type == 'plan-solve':
                        agent.run(question)
                        result = "任务已完成，请查看执行过程"
                    elif agent_type == 'react':
                        result = agent.run(question)
                    elif agent_type == 'reflection':
                        result = agent.run(question)
                        
                agent_execution_time = time.time() - agent_start_time
                logger.info(f"✅ Agent执行完成，耗时: {agent_execution_time:.2f}秒")
                
            except Exception as e:
                agent_execution_time = time.time() - agent_start_time
                logger.error(f"❌ Agent执行失败: {str(e)}")
                logger.error(f"执行耗时: {agent_execution_time:.2f}秒")
                return jsonify({
                    "error": f"Agent执行错误: {str(e)}",
                    "agent_type": agent_type,
                    "execution_time": round(agent_execution_time, 2)
                }), 500
            
            # 获取执行过程
            process_log = output_buffer.getvalue()
            
            total_time = time.time() - start_time
            logger.info(f"🎉 请求处理完成，总耗时: {total_time:.2f}秒")
            logger.info(f"=" * 60)
            
            return jsonify({
                "status": "success",
                "agent_type": agent_type,
                "response": result or "任务完成",
                "process_log": process_log,
                "execution_time": round(agent_execution_time, 2),
                "total_time": round(total_time, 2)
            })
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ 处理请求时发生错误: {str(e)}")
            logger.error(f"总耗时: {total_time:.2f}秒")
            app.logger.error(f"Error processing chat request: {str(e)}")
            return jsonify({
                "error": str(e),
                "total_time": round(total_time, 2)
            }), 500

@ns_health.route('')
class HealthResource(Resource):
    @api.response(200, '服务健康')
    @api.response(503, '服务不健康')
    def get(self):
        """健康检查接口"""
        try:
            return jsonify({
                "status": "healthy",
                "available_agents": list(agents.keys()),
                "llm_model": llm_client.model if llm_client else None
            })
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 503

@ns_chat.route('/agents')
class AgentsListResource(Resource):
    @api.response(200, '成功')
    def get(self):
        """获取可用的Agent列表"""
        agent_info = {
            "plan-solve": {
                "name": "Plan-and-Solve",
                "description": "将复杂问题分解为多个步骤，逐步解决",
                "best_for": "数学问题、多步推理、计划制定"
            },
            "react": {
                "name": "ReAct",
                "description": "结合推理和行动，可以调用外部工具",
                "best_for": "需要搜索的问题、实时信息查询"
            },
            "reflection": {
                "name": "Reflection",
                "description": "通过自我反思和迭代优化生成高质量代码",
                "best_for": "代码生成、算法优化"
            }
        }
        
        return jsonify({
            "agents": agent_info,
            "available_keys": list(agents.keys())
        })

if __name__ == '__main__':
    # 初始化所有Agent
    if init_agents():
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        print(f"\n🚀 Multi-Agent服务启动")
        print(f"📍 地址: http://{host}:{port}")
        print(f"📚 API文档: http://{host}:{port}/swagger/")
        print(f"🤖 可用Agents: {', '.join(agents.keys())}\n")
        
        app.run(host=host, port=port, debug=debug)
    else:
        print("❌ 服务启动失败：Agent初始化错误")
        sys.exit(1)
#思路：引包 → 读配置 → 创建 app → 配置数据库 → 挂载工具 → 写接口 → 启动
#todo 1:导入依赖
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
import os
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import jwt
import datetime
from functools import wraps



#todo 2:加载环境配置
load_dotenv()

#todo 3:初始化Flask实例
app = Flask(__name__)
CORS(app)   

#todo 4:数据库配置，开启跨域等中间能力
# 数据库配置
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#JWT加密密钥，正式项目放入.env中
app.config["SECRET_KEY"] = "my-secret-key-2026-demo"    

# 将唯一的 db 对象绑定到当前应用
db.init_app(app)

# 初始化迁移工具
migrate = Migrate()
migrate.init_app(app, db)

# 启动时加载模型，让迁移工具识别 User 表
from models import User,Course


#生成JWT令牌，有效期两小时
def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp" :datetime.datetime.utcnow() + datetime.timedelta(hours = 2)
    }
    token = jwt.encode(payload,app.config["SECRET_KEY"],algorithm="HS256")
    return token
    

#装饰器：给接口加上登录保护（@token_required 就相当于门禁闸机。接口就是家门，要进门必须刷合法门禁卡 (token)）
def token_required(f):
    """ f:代表被装饰的接口函数。此地就是装饰下面的register"""
    @wraps(f)
    def decorated(*args,**kwargs):
        #从请求头拿token:Authorization: Bearer xxxxxx，前端在这里存token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"msg":"缺少token,请登录"},401

        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return {"msg": "token已过期，请重新登录"}, 401
        except Exception:
            return {"msg": "token无效"}, 401
        # 将当前登录用户id传给被装饰的接口
        return f(current_user_id, *args, **kwargs)
    return decorated



#todo 6:注册路由接口
@app.route("/register",methods = ["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    #拿到前端传的role，不传就默认是studen
    role = data.get("role","student")

    #校验：只能是student和teacher
    if role not in ["student","teacher"]:
        return {"msg":"角色只能是student和teacher"},400

    if not username or not password:
        return {"msg":"用户名和密码不能为空"},400    

    exist_user = User.query.filter_by(username = username).first()
    if(exist_user):
        return{"msg":"用户名已存在"},400

    pwd_hash = generate_password_hash(password)
    new_user = User(username = username,password = pwd_hash,role = role)
    db.session.add(new_user)
    db.session.commit()
    return {"msg":"注册成功"},201

#登陆接口
@app.route("/login",methods = ["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"msg":"用户名和密码不能为空"},400    
    user = User.query.filter_by(username = username).first()
    if not user or not check_password_hash(user.password,password):
        return {"msg":"用户名或密码错误"},401

    #登录成功生成token并返回
    access_token = generate_token(user.id)
    return {
        "msg":"登录成功",
        "token": access_token,
        "user":user.to_dict()
    },200
    

#需要登录才能访问的测试接口
@app.route("/profile",methods = ["GET"])
@token_required
def profile(current_user_id):
    """获取当前登录用户信息"""
    user = User.query.get(current_user_id)
    return{
        "msg":"获取个人信息成功",
        "data":user.to_dict()
    } 

#课程接口
@app.route("/course",methods=["POST"])
@token_required
def create_course(current_user_id):
    user = User.query.get(current_user_id)

    #权限校验，只有老师可以创建课程
    if user.role != "teacher":
        return {"msg":"没有权限，仅教师可创建课程"},403

    data = request.get_json()
    name = data.get("name")
    description = data.get("description","")

    if not name:
        return{"msg":"课程名字不能为空"},400

    new_course = Course(
        name = name,
        description = description,
        teacher_id = current_user_id
    )
    db.session.add(new_course)
    db.session.commit()

    return {"msg":"课程创建成功","data":new_course.to_dict()},201
    
#获取全部课程（老师学生都可以看）
@app.route("/courses",methods=["GET"])
@token_required
def get_course_list(current_user_id):
    courses = Course.query.all()
    return{
        "msg":"获取课程列表成功",
        "data":[c.to_dict() for c in courses]
    }

#获取单门课详情
@app.route("/course/<int:course_id>",methods = ["GET"])
@token_required
def get_course_detail(current_user_id,course_id):
    course = Course.query.get(course_id)
    if not course:
        return {"msg":"该课程不存在"},404
    return {"msg":"获取课程详情成功","data":course.to_dict()},200


#路由装饰器
@app.route("/")
def index():
    return {"msg": "ok"}

#todo 7:入口判断，启动服务·
if __name__ == "__main__":
    # macOS 的 AirPlay 接收器可能占用 5000，开发服务使用 5001。
    app.run(debug=True, port=5001)

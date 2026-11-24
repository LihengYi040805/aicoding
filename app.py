# 用 Python 类，描述数据库里的一张表；告诉 SQLAlchemy：这张表叫什么、有哪些列、每一列是什么类型、有什么规则。
from extensions import db
from datetime import datetime

class Student(db.Model):
    """学生档案表"""
    __tablename__ = "students"
    id = db.Column(db.Integer,primary_key = True,autoincrement = True)
    name = db.Column(db.String(100),nullable = False)   #真实姓名
    employee_id = db.Column(db.String(50),unique = True,nullable = False)  #学号
    department = db.Column(db.String(100))  #院系
    position = db.Column(db.String(100))    #身份（大三学生等）
    created_at = db.Column(db.DateTime,default = datetime.now)

    #反向关系：一个学生对应一个User账号，uselist = False代表一对一
    user = db.relationship("User",back_populates="student",uselist = False)

    def to_dict(self):
        return{
            "id":self.id,
            "name":self.name,
            "employee_id":self.employee_id,
            "department":self.department,
            "position" : self.position
        }


class User(db.Model):
    """用户模型（用于登录认证）"""
    __tablename__ = "user"

    id = db.Column(db.Integer,primary_key = True,autoincrement = True)
    username = db.Column(db.String(80),unique = True,nullable = False)
    password = db.Column(db.String(120),nullable = False)

    #新增角色，只能是 student/teacher，默认学生
    role = db.Column(db.String(20), default = "student")

    #新增邮箱
    email = db.Column(db.String(100),unique = True,nullable = False)

    #增加外键关联students表，老师账号可以为null
    student_id = db.Column(db.Integer,db.ForeignKey("students.id"),nullable = True)

    #和Student做双向关联 ✅ 这里改成 back_populates="user"
    student = db.relationship("Student",back_populates="user")

    def to_dict(self):
        return{
            "id":self.id,
            "username":self.username,
            "role":self.role,
            "email":self.email,
            "student_id":self.student_id
        }

class Course(db.Model):
    __tablename__ = "course"
    id = db.Column(db.Integer,primary_key = True,autoincrement = True)
    name = db.Column(db.String(100),nullable = False)
    description = db.Column(db.String(255))
    teacher_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable = False)
    teacher = db.relationship("User",backref="courses")


    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name,
            "description":self.description,
            "teacher_id":self.teacher_id,
            "teacher_name":self.teacher.username if self.teacher else None
        }

class Knowledge(db.Model):
    __tablename__ = "knowledge"
    id = db.Column(db.Integer,primary_key = True,autoincrement = True)
    name = db.Column(db.String(100),nullable=False) #知识点名称
    content = db.Column(db.Text,nullable = True) #知识点详细文本
    course_id = db.Column(db.Integer,db.ForeignKey("course.id"),nullable = False) #外键，关联课程id

    #关系：一个知识点属于一门课程，Course会通过backref自动拥有knowledges属性，拿到全部子知识点
    course = db.relationship("Course",backref="knowledges")

    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name,
            "content":self.content,
            "course_id":self.course_id
        }


#知识图谱
#todo 1:知识图谱的边，描述知识点之间的关系
class KnowledgeRelation(db.Model):
    __tablename__ = "knowledge_relation"
    id = db.Column(db.Integer,primary_key = True,autoincrement = True)

    #源知识点
    source_id = db.Column(db.Integer,db.ForeignKey("knowledge.id"),nullable = False)

    #目标知识点
    target_id = db.Column(db.Integer,db.ForeignKey("knowledge.id"),nullable = False)

    #节点关系：pre（前置依赖），contain（包含），relate（相关）
    rel_type = db.Column(db.String(30),nullable = False)

    #备注
    remark = db.Column(db.String(255))

    #两个关系，分别绑定源知识点、目标知识点
    # backref="out_relation" → 知识点对象可以用 k.out_relation 拿到所有从它出发的边（和你app.py匹配！单数）
    source = db.relationship("Knowledge",foreign_keys=[source_id],backref="out_relation")
    target = db.relationship("Knowledge",foreign_keys=[target_id],backref="in_relation")

    def to_dict(self):
        return {
            "id":self.id,
            "source_id":self.source_id,
            "target_id":self.target_id,
            "rel_type":self.rel_type,
            "remark":self.remark
        }

from celery import Celery
app = Celery('crawl_task', include=['tasks'], broker='redis://127.0.0.1:6379/1',backend="redis://127.0.0.1:6379/2")
# 官方推荐使用json作为消息序列化方式
app.conf.update(
    CELERY_TIMEZONE='Asia/Shanghai',
    CELERY_ENABLE_UTC=True,
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
)
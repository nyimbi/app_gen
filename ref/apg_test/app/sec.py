from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_appbuilder.security.views import UserInfoEditView

from .models import UserExt
from .sec_forms import UserInfoEdit
from .sec_views import UserDBModelView


class UserInfoEditView(UserInfoEditView):
    form = UserInfoEdit


class MySecurityManager(SecurityManager):
    user_model = UserExt
    userdbmodelview = UserDBModelView
    userinfoeditview = UserInfoEditView

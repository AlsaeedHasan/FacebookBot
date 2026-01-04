from .actions import Comment, Follow, React, Share
from .login import Login


class Methods(Login, React, Comment, Share, Follow):
    pass

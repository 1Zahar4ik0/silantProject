from .permissions import role


def navigation(request):
    return {'user_role': role(request.user)}

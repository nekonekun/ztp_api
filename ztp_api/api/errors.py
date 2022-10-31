from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


TRANSLATIONS = {
    'value is not a valid IPv4 address': 'Это не IP-адрес',
    'unexpected value; permitted: \'newHouse\', \'newSwitch\', \'changeSwitch\'': 'Невероятная ошибка',
    'value is not a valid integer': 'Это не число',
}


def translate_error(msg: str) -> str:
    return TRANSLATIONS.get(msg, msg)


async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    response = []
    for error in errors:
        field = error['loc'][-1]
        text = error['msg']
        response.append({'field': field, 'msg': translate_error(text)})
    return JSONResponse(status_code=422, content=response)



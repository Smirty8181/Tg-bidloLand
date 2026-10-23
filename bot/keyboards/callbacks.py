from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="m"):
    a: str


class AdminCB(CallbackData, prefix="a"):
    a: str


class ConfirmCB(CallbackData, prefix="c"):
    a: str
    v: str = "1"


class IdeaCB(CallbackData, prefix="i"):
    cat: str


class ReportCB(CallbackData, prefix="r"):
    cat: str


class PunishCB(CallbackData, prefix="p"):
    a: str
    d: str = "0"

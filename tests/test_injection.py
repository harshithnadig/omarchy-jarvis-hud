import pytest
from core.inject.base import TextInjector, TextInjectionError
from core.inject.wtype import WtypeInjector
from core.inject.clipboard import SafeClipboardInjector
from core.inject.router import InjectorRouter

def test_wtype_availability():
    inj = WtypeInjector()
    # wtype is installed on this Omarchy system
    assert inj.is_available() is True

def test_clipboard_availability():
    inj = SafeClipboardInjector()
    assert inj.is_available() is True

def test_injector_router_auto():
    router = InjectorRouter(preferred_method="auto")
    inj = router.get_injector()
    assert isinstance(inj, (WtypeInjector, SafeClipboardInjector))

def test_injector_router_explicit():
    router = InjectorRouter()
    inj_wtype = router.get_injector("wtype")
    assert isinstance(inj_wtype, WtypeInjector)

    inj_clip = router.get_injector("clipboard")
    assert isinstance(inj_clip, SafeClipboardInjector)

def test_injector_router_unknown():
    router = InjectorRouter()
    with pytest.raises(TextInjectionError):
        router.get_injector("non_existent_method")

import pytest
from core.inject.base import TextInjector, TextInjectionError
from core.inject.wtype import WtypeInjector
from core.inject.clipboard import SafeClipboardInjector
from core.inject.router import InjectorRouter

def test_wtype_availability():
    inj = WtypeInjector()
    assert isinstance(inj.is_available(), bool)

def test_clipboard_availability():
    inj = SafeClipboardInjector()
    assert isinstance(inj.is_available(), bool)

def test_injector_router_auto():
    router = InjectorRouter(preferred_method="auto")
    try:
        inj = router.get_injector()
        assert isinstance(inj, (WtypeInjector, SafeClipboardInjector))
    except TextInjectionError:
        # Headless CI runner without Wayland / display
        pass

def test_injector_router_explicit():
    router = InjectorRouter()
    assert isinstance(router._injectors["wtype"], WtypeInjector)
    assert isinstance(router._injectors["clipboard"], SafeClipboardInjector)
    assert isinstance(router._injectors["ydotool"], TextInjector)

def test_injector_router_unknown():
    router = InjectorRouter()
    with pytest.raises(TextInjectionError):
        router.get_injector("non_existent_method")

def test_atspi_unlinked_truthful_failure():
    from core.inject.atspi import AtspiInjector
    inj = AtspiInjector()
    # If Python AT-SPI bindings are not available, it must not report availability
    if not inj.is_available():
        with pytest.raises(TextInjectionError):
            inj.inject("test text")

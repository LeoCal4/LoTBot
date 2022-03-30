import gettext

_ = gettext.gettext
current_language = "en"


def update_language(language: str):
    global _
    global current_language
    print(f"============= UPDATING LANGUAGE WITH LANGUAGE {language} ==================")
    if current_language == language:
        return
    current_language = language
    new_lang = gettext.translation("base", localedir="locales", languages=[language])
    # new_lang.install()
    _ = new_lang.gettext


def get_translator(language: str = current_language) -> gettext.gettext:
    if language:
        update_language(language)
    return _

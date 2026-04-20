import re
import stroke_data

class InputValidator:
    _stroke_manager = None

    @classmethod
    def _get_stroke_manager(cls):
        if cls._stroke_manager is None:
            cls._stroke_manager = stroke_data.get_default_manager()
        return cls._stroke_manager

    @staticmethod
    def validate_characters(characters):
        if not characters:
            return False, '错误：输入不能为空，请输入需要生成字帖的汉字。'
        
        if not isinstance(characters, str):
            return False, '错误：输入类型不正确，请输入字符串类型的汉字。'
        
        if characters.strip() == '':
            return False, '错误：输入不能只包含空白字符，请输入有效的汉字。'
        
        cleaned = characters.strip()
        
        if len(cleaned) < 1:
            return False, '错误：输入字数不足，请至少输入1个汉字。'
        
        chinese_pattern = re.compile(r'^[\u4e00-\u9fff]+$')
        if not chinese_pattern.match(cleaned):
            non_chinese = []
            for idx, char in enumerate(cleaned):
                if not ('\u4e00' <= char <= '\u9fff'):
                    non_chinese.append(f'第{idx+1}个字符"{char}"')
            if non_chinese:
                return False, f'错误：输入包含非汉字字符：{", ".join(non_chinese)}。请只输入汉字。'
        
        return True, cleaned

    @staticmethod
    def get_stroke_order(char):
        manager = InputValidator._get_stroke_manager()
        return manager.get_stroke_order(char)

    @staticmethod
    def get_available_chars_count():
        manager = InputValidator._get_stroke_manager()
        return manager.get_available_chars_count()

    @staticmethod
    def add_to_database(char, strokes):
        manager = InputValidator._get_stroke_manager()
        return manager.add_to_local_database(char, strokes)

    @staticmethod
    def validate_page_range(page_number, total_pages):
        if page_number < 1:
            return False, f'错误：页码不能小于1。'
        if page_number > total_pages:
            return False, f'错误：页码{page_number}超出范围，总共有{total_pages}页。'
        return True, None

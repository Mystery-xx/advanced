#!/usr/bin/env python3
"""
Stage 1: Input Analyzer

Extracts key phrases, sentiment markers, and review metadata from input text.
"""

from finetune.multi_stage.base import Stage, StageInput, StageOutput


# Russian sentiment words for marker detection (expanded)
POSITIVE_WORDS = {
    # Basic positive adjectives
    'отличный', 'отличная', 'отличное', 'отличные',
    'хороший', 'хорошая', 'хорошее', 'хорошие',
    'превосходный', 'превосходная', 'превосходное',
    'замечательный', 'замечательная', 'замечательное',
    'прекрасный', 'прекрасная', 'прекрасное',
    'великолепный', 'великолепная', 'великолепное',
    'лучший', 'лучшая', 'лучшее', 'лучшие',
    'крепкий', 'крепкая', 'крепкое', 'крепкие',
    'удобный', 'удобная', 'удобное', 'удобные',
    'надёжный', 'надёжная', 'надёжное', 'надёжные',
    'качественный', 'качественная', 'качественное',
    # Strong positive emotions
    'восхитительный', 'восхитительная', 'восхитительное',
    'изумительный', 'изумительная', 'изумительное',
    'потрясающий', 'потрясающая', 'потрясающее',
    'фантастический', 'фантастическая', 'фантастическое',
    'идеальный', 'идеальная', 'идеальное',
    'безупречный', 'безупречная', 'безупречное',
    'совершенный', 'совершенная', 'совершенное',
    # Satisfaction
    'доволен', 'довольна', 'довольно', 'довольный',
    'счастлив', 'счастлива', 'счастливый',
    'рад', 'рада', 'радый',
    'восхищён', 'восхищена', 'восхищённый',
    'благодарен', 'благодарна', 'признателен', 'признательна',
    # Recommendations
    'рекомендую', 'советую', 'рекомендуем', 'советуем',
    'стоит', 'стоит брать', 'стоит покупать',
    'берите', 'покупайте', 'заказывайте',
    'топ', 'огонь', 'пушка', 'супер', 'класс', 'круто',
    # Liking
    'нравится', 'понравилось', 'понравился', 'понравилась',
    'люблю', 'полюбил', 'полюбила',
    'в восторге', 'в полном восторге',
    # Quality descriptors
    'выносливый', 'выносливая', 'выносливое',
    'устойчивый', 'устойчивая', 'устойчивое',
    'комфортный', 'комфортная', 'комфортное',
    'практичный', 'практичная', 'практичное',
    'функциональный', 'функциональная', 'функциональное',
    'эргономичный', 'эргономичная', 'эргономичное',
    'стильный', 'стильная', 'стильное',
    'красивый', 'красивая', 'красивое',
    'современный', 'современная', 'современное',
    # Service/delivery
    'быстрый', 'быстрая', 'быстрое', 'быстро',
    'оперативный', 'оперативная', 'оперативно',
    'вежливый', 'вежливая', 'вежливый персонал',
    'профессиональный', 'профессиональная', 'профессионалы',
    # Value
    'выгодный', 'выгодная', 'выгодное', 'выгодно',
    'доступный', 'доступная', 'доступное', 'доступно',
    'недорогой', 'недорогая', 'недорогое',
    'цена соответствует', 'стоит своих денег',
    # General positive
    'успех', 'удача', 'повезло',
    'спасибо', 'благодарю', 'признательность',
    'позитив', 'позитивный', 'приятный', 'приятно',
}

NEGATIVE_WORDS = {
    # Basic negative adjectives
    'плохой', 'плохая', 'плохое', 'плохие',
    'ужасный', 'ужасная', 'ужасное', 'ужасные',
    'отвратительный', 'отвратительная', 'отвратительное',
    'негативный', 'негативная', 'негативное',
    'кошмарный', 'кошмарная', 'кошмарное',
    'жестяной', 'жестяная', 'жестяное',
    'ужас', 'жуть', 'кошмар', 'ад',
    # Broken/defective
    'развалился', 'развалилась', 'развалилось',
    'сломался', 'сломалась', 'сломалось', 'сломался',
    'ржавчина', 'ржавый', 'ржавая', 'поржавел',
    'трещина', 'треснул', 'треснула', 'треснуло',
    'дефект', 'дефектный', 'брак', 'бракованный',
    'неисправный', 'не работает', 'не функционирует',
    # Disappointment
    'разочарован', 'разочарована', 'разочарование',
    'расстроен', 'расстроена', 'расстройство',
    'огорчён', 'огорчена', 'печаль', 'грустно',
    'жалко', 'жаль', 'сожаление',
    # Returns/refunds
    'вернул', 'вернула', 'вернули',
    'сдал', 'сдала', 'сдали',
    'возврат', 'вернуть', 'деньги на ветер',
    'потратил впустую', 'выброшенные деньги',
    # Not recommending
    'не рекомендую', 'не советую', 'не советуем',
    'избегайте', 'не берите', 'не покупайте',
    'не стоит', 'не рекомендую покупать',
    'лучше не надо', 'проходите мимо',
    # Trash/junk
    'мусор', 'хлам', 'дрянь', 'ерунда',
    'бесполезный', 'бесполезная', 'бесполезное',
    'ненужный', 'ненужная', 'ненужное',
    # Quality issues
    'дешёвый', 'дешёвая', 'дешёвое', 'дешево',
    'некачественный', 'некачественная', 'некачественное',
    'хлипкий', 'хлипкая', 'хлипкое',
    'мягкий', 'мягкая', 'мягкое',  # in context of wheels
    'гнётся', 'гнётся', 'погнулся',
    'люфт', 'люфтит', 'шатается',
    # Specific failures
    'спускает', 'спускается', 'сдулся',
    'ослабевают', 'ослаб', 'ослабла',
    'провис', 'провисло', 'провисла',
    'лопнул', 'лопнула', 'лопнуло',
    'облетает', 'облез', 'облезла',
    'отклеился', 'отклеилась', 'отвалился',
    'поцарапанный', 'помятый', 'побитый',
    # Problems/issues
    'недостаток', 'недостатки', 'минус', 'минусы',
    'проблема', 'проблемы', 'проблемный',
    'вопрос', 'вопросы', 'нарекания',
    'сложность', 'сложности', 'трудность',
    # Service/delivery issues
    'медленный', 'медленная', 'медленное', 'медленно',
    'долгая доставка', 'задержка', 'опоздал',
    'грубый', 'грубая', 'хамство', 'нагрубили',
    'невежливый', 'невежливая', 'непрофессиональный',
    # Value issues
    'дорогой', 'дорогая', 'дорогое', 'дорого',
    'завышенная цена', 'не стоит', 'переоценён',
    'обман', 'обманули', 'впаривают',
    # General negative
    'катастрофа', 'провал', 'фиаско',
    'отрицательный', 'негатив', 'расстройство',
    'кошмар', 'ужас', 'жесть', 'ад',
}


class Stage1Analyzer(Stage):
    """
    Stage 1: Input Analyzer
    
    Extracts key phrases, sentiment markers, and metadata from review text.
    """
    
    @property
    def name(self) -> str:
        return "stage1_analyzer"
    
    def analyze(self, review_text: str) -> dict:
        """
        Analyze review text and extract key information.
        
        Args:
            review_text: The review text to analyze
            
        Returns:
            dict with keys:
                - key_phrases: list of important nouns and adjectives
                - markers: dict with 'positive' and 'negative' word lists
                - metadata: dict with text statistics
        """
        if not review_text or not review_text.strip():
            return {
                'key_phrases': [],
                'markers': {'positive': [], 'negative': []},
                'metadata': {'length': 0, 'word_count': 0}
            }
        
        # Tokenize: simple split on whitespace and punctuation
        words = self._tokenize(review_text)
        
        # Extract key phrases (nouns and adjectives - simplified approach)
        key_phrases = self._extract_key_phrases(words, review_text)
        
        # Detect sentiment markers
        markers = self._detect_sentiment_markers(words)
        
        # Extract metadata
        metadata = self._extract_metadata(review_text, words)
        
        return {
            'key_phrases': key_phrases,
            'markers': markers,
            'metadata': metadata
        }
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """
        Execute the analysis stage.
        
        Args:
            input_data: StageInput with data containing review_text
            
        Returns:
            StageOutput with analysis result
        """
        try:
            review_text = input_data.data
            if not isinstance(review_text, str):
                return StageOutput(
                    result=None,
                    success=False,
                    error_message="Input data must be a string (review text)"
                )
            
            result = self.analyze(review_text)
            return StageOutput(result=result, success=True)
            
        except Exception as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=f"Analysis failed: {str(e)}"
            )
    
    def _tokenize(self, text: str) -> list[str]:
        """
        Simple tokenization: split on whitespace and punctuation.
        
        Args:
            text: Input text
            
        Returns:
            List of lowercase words
        """
        import re
        # Split on non-letter characters (keep Russian letters)
        words = re.findall(r'[а-яА-ЯёЁa-zA-Z]+', text)
        return [w.lower() for w in words]
    
    def _extract_key_phrases(self, words: list[str], original_text: str) -> list[str]:
        """
        Extract key phrases (nouns and adjectives).
        
        Simplified approach: take unique content words, excluding common stop words.
        
        Args:
            words: List of tokenized words
            original_text: Original text for context
            
        Returns:
            List of key phrases
        """
        # Russian stop words (common function words)
        stop_words = {
            'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то',
            'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за',
            'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще',
            'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли',
            'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь',
            'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей',
            'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя',
            'их', 'им', 'более', 'всегда', 'конечно', 'всю', 'между', 'этого', 'этот',
            'эта', 'это', 'эти', 'этим', 'этом', 'этой', 'эту', 'этого', 'этому',
            'который', 'которая', 'которое', 'которые', 'свой', 'своя', 'свое',
            'чуть', 'раз', 'под', 'через', 'без', 'при', 'над', 'для', 'перед',
            'после', 'над', 'под', 'за', 'перед', 'через', 'между', 'вокруг',
            'чтобы', 'какой', 'какая', 'какое', 'какие', 'какого', 'какую',
            'такой', 'такая', 'такое', 'такие', 'сама', 'само', 'сами', 'сам',
            'самый', 'самая', 'самое', 'самые',
        }
        
        # Extract content words (non-stop words, length > 2)
        key_phrases = []
        seen = set()
        
        for word in words:
            if word not in stop_words and len(word) > 2 and word not in seen:
                key_phrases.append(word)
                seen.add(word)
        
        return key_phrases
    
    def _detect_sentiment_markers(self, words: list[str]) -> dict[str, list[str]]:
        """
        Detect sentiment markers (positive/negative words).
        
        Args:
            words: List of tokenized words
            
        Returns:
            dict with 'positive' and 'negative' lists
        """
        positive = []
        negative = []
        
        for word in words:
            if word in POSITIVE_WORDS:
                positive.append(word)
            elif word in NEGATIVE_WORDS:
                negative.append(word)
        
        return {
            'positive': positive,
            'negative': negative
        }
    
    def _extract_metadata(self, text: str, words: list[str]) -> dict:
        """
        Extract metadata about the text.
        
        Args:
            text: Original text
            words: List of tokenized words
            
        Returns:
            dict with metadata
        """
        # Simple language detection based on Cyrillic characters
        cyrillic_count = sum(1 for c in text if 'а' <= c <= 'я' or 'А' <= c <= 'Я' or c == 'ё' or c == 'Ё')
        latin_count = sum(1 for c in text if 'a' <= c <= 'z' or 'A' <= c <= 'Z')
        
        language = 'ru' if cyrillic_count > latin_count else 'en' if latin_count > 0 else 'unknown'
        
        return {
            'length': len(text),
            'word_count': len(words),
            'language': language,
            'char_count_no_spaces': len(text.replace(' ', '')),
            'avg_word_length': round(sum(len(w) for w in words) / len(words), 2) if words else 0
        }
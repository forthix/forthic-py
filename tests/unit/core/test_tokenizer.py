"""Tests for Forthic tokenizer."""

import pytest

from forthic import (
    CodeLocation,
    InvalidWordNameError,
    Tokenizer,
    TokenType,
    UnterminatedStringError,
)


class TestBasicTokenization:
    """Test basic token types."""

    def test_word_tokens(self) -> None:
        tokenizer = Tokenizer("HELLO WORLD")
        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "HELLO"

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "WORLD"

        token = tokenizer.next_token()
        assert token.type == TokenType.EOS

    def test_string_tokens(self) -> None:
        tokenizer = Tokenizer('"Hello World"')
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.string == "Hello World"

    def test_triple_quote_string(self) -> None:
        tokenizer = Tokenizer('"""Line 1\nLine 2"""')
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.string == "Line 1\nLine 2"

    def test_comment_token(self) -> None:
        tokenizer = Tokenizer("# This is a comment\nWORD")
        token = tokenizer.next_token()
        assert token.type == TokenType.COMMENT

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "WORD"

    def test_array_tokens(self) -> None:
        tokenizer = Tokenizer("[1 2 3]")
        token = tokenizer.next_token()
        assert token.type == TokenType.START_ARRAY

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "1"

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "2"

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "3"

        token = tokenizer.next_token()
        assert token.type == TokenType.END_ARRAY

    def test_definition_tokens(self) -> None:
        tokenizer = Tokenizer(": DOUBLE 2 * ;")
        token = tokenizer.next_token()
        assert token.type == TokenType.START_DEF
        assert token.string == "DOUBLE"

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "2"

        token = tokenizer.next_token()
        assert token.type == TokenType.WORD
        assert token.string == "*"

        token = tokenizer.next_token()
        assert token.type == TokenType.END_DEF

    def test_module_tokens(self) -> None:
        tokenizer = Tokenizer("{mymodule : WORD 42 ; }")
        token = tokenizer.next_token()
        assert token.type == TokenType.START_MODULE
        assert token.string == "mymodule"

        token = tokenizer.next_token()
        assert token.type == TokenType.START_DEF
        assert token.string == "WORD"

        # Skip to end
        while token.type != TokenType.END_MODULE:
            token = tokenizer.next_token()
        assert token.type == TokenType.END_MODULE

    def test_dot_symbol(self) -> None:
        tokenizer = Tokenizer(".key .value")
        token = tokenizer.next_token()
        assert token.type == TokenType.DOT_SYMBOL
        assert token.string == "key"

        token = tokenizer.next_token()
        assert token.type == TokenType.DOT_SYMBOL
        assert token.string == "value"

    def test_memo_token(self) -> None:
        tokenizer = Tokenizer("@: DATA [ 1 2 3 ] ;")
        token = tokenizer.next_token()
        assert token.type == TokenType.START_MEMO
        assert token.string == "DATA"


class TestTokenizerEdgeCases:
    """Test edge cases and special scenarios."""

    def test_whitespace_handling(self) -> None:
        tokenizer = Tokenizer("  WORD1   WORD2  \n  WORD3  ")
        token = tokenizer.next_token()
        assert token.string == "WORD1"

        token = tokenizer.next_token()
        assert token.string == "WORD2"

        token = tokenizer.next_token()
        assert token.string == "WORD3"

    def test_empty_string(self) -> None:
        tokenizer = Tokenizer("")
        token = tokenizer.next_token()
        assert token.type == TokenType.EOS

    def test_only_whitespace(self) -> None:
        tokenizer = Tokenizer("   \n  \t  ")
        token = tokenizer.next_token()
        assert token.type == TokenType.EOS


class TestTokenPositions:
    """Test token position tracking."""

    def test_knows_token_positions(self) -> None:
        """Test that tokenizer tracks token positions correctly."""
        main_forthic = """
    : ADD-ONE   1 23 +;
    {module
        # 2 ADD-ONE
    }
    @: MY-MEMO   [ "hello" '''triple-single-quoted-string'''];
    """

        reference_location = CodeLocation(
            source="main",
            line=1,
            column=1,
            start_pos=0,
        )

        tokenizer = Tokenizer(main_forthic, reference_location)

        # TOK_START_DEF
        begin_def = tokenizer.next_token()
        assert begin_def.location.line == 2
        assert begin_def.location.column == 7
        assert begin_def.location.source == "main"
        assert begin_def.location.start_pos == 7

        # TOK_WORD: 1
        one_token = tokenizer.next_token()
        assert one_token.location.line == 2
        assert one_token.location.column == 17
        assert one_token.location.start_pos == 17

        # TOK_WORD: 23
        token_23 = tokenizer.next_token()
        assert token_23.location.line == 2
        assert token_23.location.column == 19
        assert token_23.location.start_pos == 19

        # TOK_WORD: +
        plus_token = tokenizer.next_token()
        assert plus_token.location.line == 2
        assert plus_token.location.column == 22
        assert plus_token.location.start_pos == 22

    def test_knows_token_location_in_ad_hoc_string(self) -> None:
        """Test token location tracking in ad hoc string with reference."""
        reference_location = CodeLocation(
            source="main",
            line=21,
            column=15,
            start_pos=67,
        )

        main_forthic = "'key' REC@ LOWERCASE"

        tokenizer = Tokenizer(main_forthic, reference_location)

        # 'key'
        token = tokenizer.next_token()
        assert token.string == "key"
        assert token.location.line == 21
        assert token.location.column == 16
        assert token.location.source == "main"
        assert token.location.start_pos == 68

        # REC@
        token = tokenizer.next_token()
        assert token.string == "REC@"
        assert token.location.line == 21
        assert token.location.column == 21
        assert token.location.start_pos == 73

        # LOWERCASE
        token = tokenizer.next_token()
        assert token.string == "LOWERCASE"
        assert token.location.line == 21
        assert token.location.column == 26
        assert token.location.start_pos == 78


class TestErrorCases:
    """Test error cases."""

    def test_invalid_word_name(self) -> None:
        """Test that invalid word names raise error."""
        reference_location = CodeLocation(
            source="main",
            line=1,
            column=1,
            start_pos=0,
        )

        main_forthic = ": John's-Word   1 23 +;"

        with pytest.raises(InvalidWordNameError):
            tokenizer = Tokenizer(main_forthic, reference_location)
            tokenizer.next_token()

    def test_unterminated_string(self) -> None:
        """Test that unterminated strings raise error."""
        reference_location = CodeLocation(
            source="main",
            line=1,
            column=1,
            start_pos=0,
        )

        main_forthic = "'key"

        with pytest.raises(UnterminatedStringError):
            tokenizer = Tokenizer(main_forthic, reference_location)
            tokenizer.next_token()


class TestTripleQuoteStringsWithNestedQuotes:
    """Test triple quote strings with nested quotes."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.reference_location = CodeLocation(
            source="test",
            line=1,
            column=1,
            start_pos=0,
        )

    def test_basic_nested_quotes(self) -> None:
        """Test basic case: '''I said 'Hello''''"""
        input_str = "'''I said 'Hello''''"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == "I said 'Hello'"

    def test_normal_triple_quote_behavior(self) -> None:
        """Test normal triple quote behavior (no 4+ consecutive quotes)."""
        input_str = "'''Hello'''"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == "Hello"

    def test_double_quotes_with_greedy_mode(self) -> None:
        """Test double quotes with greedy mode."""
        input_str = '"""I said "Hello""""'
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == 'I said "Hello"'

    def test_six_consecutive_quotes(self) -> None:
        """Test six consecutive quotes (empty string case)."""
        input_str = "''''''"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == ""

    def test_eight_consecutive_quotes(self) -> None:
        """Test eight consecutive quotes (two quote content)."""
        input_str = "''''''''"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == "''"

    def test_multiple_nested_quotes(self) -> None:
        """Test multiple nested quotes."""
        input_str = """\"\"\"He said "I said 'Hello' to you\"\"\"\""""
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == """He said "I said 'Hello' to you\""""

    def test_content_with_apostrophes(self) -> None:
        """Test content with apostrophes (contractions)."""
        input_str = "'''It's a beautiful day, isn't it?''''"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.string == "It's a beautiful day, isn't it?'"

    def test_mixed_quote_types_dont_trigger_greedy_mode(self) -> None:
        """Test that mixed quote types don't trigger greedy mode."""
        input_str = "'''Hello\"\"\""

        with pytest.raises(UnterminatedStringError):
            tokenizer = Tokenizer(input_str, self.reference_location)
            tokenizer.next_token()


class TestDotSymbolTokenization:
    """Test dot symbol tokenization."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.reference_location = CodeLocation(
            source="test",
            line=1,
            column=1,
            start_pos=0,
        )

    def test_basic_dot_symbol(self) -> None:
        """Test basic dot symbol: .symbol"""
        input_str = ".symbol"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.type == TokenType.DOT_SYMBOL
        assert token.string == "symbol"

    def test_dot_symbol_with_numbers_and_hyphens(self) -> None:
        """Test dot symbol with numbers and hyphens: .symbol-123"""
        input_str = ".symbol-123"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.type == TokenType.DOT_SYMBOL
        assert token.string == "symbol-123"

    def test_dot_symbol_with_underscores(self) -> None:
        """Test dot symbol with underscores: .my_symbol_123"""
        input_str = ".my_symbol_123"
        tokenizer = Tokenizer(input_str, self.reference_location)
        token = tokenizer.next_token()

        assert token.type == TokenType.DOT_SYMBOL
        assert token.string == "my_symbol_123"

    def test_dot_symbol_terminated_by_whitespace(self) -> None:
        """Test dot symbol terminated by whitespace."""
        input_str = ".symbol NEXT"
        tokenizer = Tokenizer(input_str, self.reference_location)

        token1 = tokenizer.next_token()
        assert token1.type == TokenType.DOT_SYMBOL
        assert token1.string == "symbol"

        token2 = tokenizer.next_token()
        assert token2.type == TokenType.WORD
        assert token2.string == "NEXT"

    def test_dot_symbol_terminated_by_array_bracket(self) -> None:
        """Test dot symbol terminated by array bracket."""
        input_str = ".symbol]"
        tokenizer = Tokenizer(input_str, self.reference_location)

        token1 = tokenizer.next_token()
        assert token1.type == TokenType.DOT_SYMBOL
        assert token1.string == "symbol"

        token2 = tokenizer.next_token()
        assert token2.type == TokenType.END_ARRAY
        assert token2.string == "]"

    def test_dot_symbol_in_array(self) -> None:
        """Test dot symbol in array: [.symbol1 .symbol2]"""
        input_str = "[.symbol1 .symbol2]"
        tokenizer = Tokenizer(input_str, self.reference_location)

        tokens = []
        token = tokenizer.next_token()
        while token.type != TokenType.EOS:
            tokens.append(token)
            token = tokenizer.next_token()

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.START_ARRAY
        assert tokens[1].type == TokenType.DOT_SYMBOL
        assert tokens[1].string == "symbol1"
        assert tokens[2].type == TokenType.DOT_SYMBOL
        assert tokens[2].string == "symbol2"
        assert tokens[3].type == TokenType.END_ARRAY

    def test_just_dot_by_itself_is_word(self) -> None:
        """Test that just a dot by itself should be treated as a word."""
        input_str = ". NEXT"
        tokenizer = Tokenizer(input_str, self.reference_location)

        token1 = tokenizer.next_token()
        assert token1.type == TokenType.WORD
        assert token1.string == "."

        token2 = tokenizer.next_token()
        assert token2.type == TokenType.WORD
        assert token2.string == "NEXT"

    def test_one_character_dot_symbols(self) -> None:
        """Test that one-character dot symbols (.s, .S, .x) should be DOT_SYMBOL."""
        input_str = ".s .S .x"
        tokenizer = Tokenizer(input_str, self.reference_location)

        token1 = tokenizer.next_token()
        assert token1.type == TokenType.DOT_SYMBOL
        assert token1.string == "s"

        token2 = tokenizer.next_token()
        assert token2.type == TokenType.DOT_SYMBOL
        assert token2.string == "S"

        token3 = tokenizer.next_token()
        assert token3.type == TokenType.DOT_SYMBOL
        assert token3.string == "x"

    def test_two_character_dot_symbol(self) -> None:
        """Test that two-character dot symbol (.ab) should be DOT_SYMBOL."""
        input_str = ".ab NEXT"
        tokenizer = Tokenizer(input_str, self.reference_location)

        token1 = tokenizer.next_token()
        assert token1.type == TokenType.DOT_SYMBOL
        assert token1.string == "ab"

        token2 = tokenizer.next_token()
        assert token2.type == TokenType.WORD
        assert token2.string == "NEXT"

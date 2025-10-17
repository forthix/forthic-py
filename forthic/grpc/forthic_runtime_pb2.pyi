from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecuteWordRequest(_message.Message):
    __slots__ = ("word_name", "stack")
    WORD_NAME_FIELD_NUMBER: _ClassVar[int]
    STACK_FIELD_NUMBER: _ClassVar[int]
    word_name: str
    stack: _containers.RepeatedCompositeFieldContainer[StackValue]
    def __init__(self, word_name: _Optional[str] = ..., stack: _Optional[_Iterable[_Union[StackValue, _Mapping]]] = ...) -> None: ...

class ExecuteWordResponse(_message.Message):
    __slots__ = ("result_stack", "error")
    RESULT_STACK_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    result_stack: _containers.RepeatedCompositeFieldContainer[StackValue]
    error: ErrorInfo
    def __init__(self, result_stack: _Optional[_Iterable[_Union[StackValue, _Mapping]]] = ..., error: _Optional[_Union[ErrorInfo, _Mapping]] = ...) -> None: ...

class ExecuteSequenceRequest(_message.Message):
    __slots__ = ("word_names", "stack")
    WORD_NAMES_FIELD_NUMBER: _ClassVar[int]
    STACK_FIELD_NUMBER: _ClassVar[int]
    word_names: _containers.RepeatedScalarFieldContainer[str]
    stack: _containers.RepeatedCompositeFieldContainer[StackValue]
    def __init__(self, word_names: _Optional[_Iterable[str]] = ..., stack: _Optional[_Iterable[_Union[StackValue, _Mapping]]] = ...) -> None: ...

class ExecuteSequenceResponse(_message.Message):
    __slots__ = ("result_stack", "error")
    RESULT_STACK_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    result_stack: _containers.RepeatedCompositeFieldContainer[StackValue]
    error: ErrorInfo
    def __init__(self, result_stack: _Optional[_Iterable[_Union[StackValue, _Mapping]]] = ..., error: _Optional[_Union[ErrorInfo, _Mapping]] = ...) -> None: ...

class StackValue(_message.Message):
    __slots__ = ("int_value", "string_value", "bool_value", "float_value", "null_value", "array_value", "record_value", "instant_value", "plain_date_value", "zoned_datetime_value")
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    NULL_VALUE_FIELD_NUMBER: _ClassVar[int]
    ARRAY_VALUE_FIELD_NUMBER: _ClassVar[int]
    RECORD_VALUE_FIELD_NUMBER: _ClassVar[int]
    INSTANT_VALUE_FIELD_NUMBER: _ClassVar[int]
    PLAIN_DATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    ZONED_DATETIME_VALUE_FIELD_NUMBER: _ClassVar[int]
    int_value: int
    string_value: str
    bool_value: bool
    float_value: float
    null_value: NullValue
    array_value: ArrayValue
    record_value: RecordValue
    instant_value: InstantValue
    plain_date_value: PlainDateValue
    zoned_datetime_value: ZonedDateTimeValue
    def __init__(self, int_value: _Optional[int] = ..., string_value: _Optional[str] = ..., bool_value: bool = ..., float_value: _Optional[float] = ..., null_value: _Optional[_Union[NullValue, _Mapping]] = ..., array_value: _Optional[_Union[ArrayValue, _Mapping]] = ..., record_value: _Optional[_Union[RecordValue, _Mapping]] = ..., instant_value: _Optional[_Union[InstantValue, _Mapping]] = ..., plain_date_value: _Optional[_Union[PlainDateValue, _Mapping]] = ..., zoned_datetime_value: _Optional[_Union[ZonedDateTimeValue, _Mapping]] = ...) -> None: ...

class NullValue(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ArrayValue(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[StackValue]
    def __init__(self, items: _Optional[_Iterable[_Union[StackValue, _Mapping]]] = ...) -> None: ...

class RecordValue(_message.Message):
    __slots__ = ("fields",)
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StackValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[StackValue, _Mapping]] = ...) -> None: ...
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.MessageMap[str, StackValue]
    def __init__(self, fields: _Optional[_Mapping[str, StackValue]] = ...) -> None: ...

class InstantValue(_message.Message):
    __slots__ = ("iso8601",)
    ISO8601_FIELD_NUMBER: _ClassVar[int]
    iso8601: str
    def __init__(self, iso8601: _Optional[str] = ...) -> None: ...

class PlainDateValue(_message.Message):
    __slots__ = ("iso8601_date",)
    ISO8601_DATE_FIELD_NUMBER: _ClassVar[int]
    iso8601_date: str
    def __init__(self, iso8601_date: _Optional[str] = ...) -> None: ...

class ZonedDateTimeValue(_message.Message):
    __slots__ = ("iso8601", "timezone")
    ISO8601_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    iso8601: str
    timezone: str
    def __init__(self, iso8601: _Optional[str] = ..., timezone: _Optional[str] = ...) -> None: ...

class ErrorInfo(_message.Message):
    __slots__ = ("message", "runtime", "stack_trace", "error_type", "word_location", "module_name", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    STACK_TRACE_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    WORD_LOCATION_FIELD_NUMBER: _ClassVar[int]
    MODULE_NAME_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    message: str
    runtime: str
    stack_trace: _containers.RepeatedScalarFieldContainer[str]
    error_type: str
    word_location: str
    module_name: str
    context: _containers.ScalarMap[str, str]
    def __init__(self, message: _Optional[str] = ..., runtime: _Optional[str] = ..., stack_trace: _Optional[_Iterable[str]] = ..., error_type: _Optional[str] = ..., word_location: _Optional[str] = ..., module_name: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ListModulesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListModulesResponse(_message.Message):
    __slots__ = ("modules",)
    MODULES_FIELD_NUMBER: _ClassVar[int]
    modules: _containers.RepeatedCompositeFieldContainer[ModuleSummary]
    def __init__(self, modules: _Optional[_Iterable[_Union[ModuleSummary, _Mapping]]] = ...) -> None: ...

class ModuleSummary(_message.Message):
    __slots__ = ("name", "description", "word_count", "runtime_specific")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    WORD_COUNT_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_SPECIFIC_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    word_count: int
    runtime_specific: bool
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., word_count: _Optional[int] = ..., runtime_specific: bool = ...) -> None: ...

class GetModuleInfoRequest(_message.Message):
    __slots__ = ("module_name",)
    MODULE_NAME_FIELD_NUMBER: _ClassVar[int]
    module_name: str
    def __init__(self, module_name: _Optional[str] = ...) -> None: ...

class GetModuleInfoResponse(_message.Message):
    __slots__ = ("name", "description", "words")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    WORDS_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    words: _containers.RepeatedCompositeFieldContainer[WordInfo]
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., words: _Optional[_Iterable[_Union[WordInfo, _Mapping]]] = ...) -> None: ...

class WordInfo(_message.Message):
    __slots__ = ("name", "stack_effect", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    STACK_EFFECT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    stack_effect: str
    description: str
    def __init__(self, name: _Optional[str] = ..., stack_effect: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

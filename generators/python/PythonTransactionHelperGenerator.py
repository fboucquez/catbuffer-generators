from generators.python.Helpers import indent, NAME_VALUE_SUFFIX


# pylint: disable=too-few-public-methods
class PythonTransactionHelperGenerator:
    """Python transaction helper class generator"""

    def __init__(self, class_name, entityType_enum_value, embedded):
        self.class_output = []
        self.class_name = class_name
        self.imports = []
        self.embedded = embedded
        if self.embedded:
            self.imports += ['from functools import reduce']
            self.imports += ['from typing import List']
        self.enum_list = entityType_enum_value
        self._add_import('EntityTypeDto')
        if self.embedded:
            self._add_import('EmbeddedTransactionBuilder')
            self._add_import('GeneratorUtils')
        else:
            self._add_import('TransactionBuilder')

    def _read_file(self):
        loadFromBinary_method = self._write_loadFromBinary_method()  # also adds the imports
        self.class_output += sorted(self.imports)
        self.class_output += [''] + ['']  # add 2 blank lines
        line = ['class {0}:'.format(self.class_name)]
        line += [indent('"""Helper class for {0}transaction serialization"""'.format('embedded ' if self.embedded else ''), 1)]
        line += ['']
        line += loadFromBinary_method
        line += ['']
        if self.embedded:
            line += self._write_serialize_embedded_transaction_method()
            line += ['']
            line += self._write_size_getter()
        self.class_output += line

    @classmethod
    def _write_serialize_embedded_transaction_method(cls):
        line = [indent('@classmethod')]
        line += [indent('def serialize(cls, transaction: EmbeddedTransactionBuilder) -> bytes:')]
        line += [indent('"""Serialize an embedded transaction"""', 2)]
        line += [indent('bytes_ = transaction.serialize()', 2)]
        line += [indent('padding = bytes(GeneratorUtils.getTransactionPaddingSize(len(bytes_), 8))', 2)]
        line += [indent('return GeneratorUtils.concatTypedArrays(bytes_, padding)', 2)]
        return line

    def _write_loadFromBinary_method(self):
        if self.embedded:
            line = [indent('@classmethod')]
            line += [indent('def loadFromBinary(cls, payload: bytes) -> EmbeddedTransactionBuilder:')]
            line += [indent('"""Deserialize an embedded transaction from binary"""', 2)]
            line += [indent('header = EmbeddedTransactionBuilder.loadFromBinary(payload)', 2)]
        else:
            line = [indent('@classmethod')]
            line += [indent('def loadFromBinary(cls, payload: bytes) -> TransactionBuilder:')]
            line += [indent('"""Deserialize a transaction from binary"""', 2)]
            line += [indent('header = TransactionBuilder.loadFromBinary(payload)', 2)]

        line += [indent('entityType = header.getType' + NAME_VALUE_SUFFIX + '()', 2)]
        if_clause = 'if'
        for name, value_comments in self.enum_list.items():
            # pylint: disable=unused-variable
            value, comments = value_comments
            builder_class = None
            if value != 0 and not name.upper().startswith('AGGREGATE') and self.embedded:
                builder_class = 'Embedded{0}'.format(''.join([a.capitalize() for a in name.split('_')]))
            elif value != 0 and not self.embedded:
                builder_class = '{0}'.format(''.join([a.capitalize() for a in name.split('_')]))
            if builder_class is not None:
                self._add_import(builder_class)
                line += [indent('{0} entityType == EntityTypeDto.{1}:'.format(if_clause, name), 2)]
                line += [indent('return {0}.loadFromBinary(payload)'.format(builder_class), 3)]
                if_clause = 'elif'
        line += [indent('else:', 2)]
        line += [indent('raise Exception(\'Transaction type: {0} not recognized.\'.format(entityType))', 3)]
        return line

    @classmethod
    def _write_size_getter(cls):
        line = [indent('@classmethod')]
        line += [indent('def getEmbeddedTransactionSize(cls, transactions: List[EmbeddedTransactionBuilder]) -> int:')]
        line += [indent('"""Get actual embedded transaction size"""', 2)]
        line += [indent(
            'return reduce(lambda a, b: a + b, map(lambda x: len(EmbeddedTransactionHelper.serialize(x)), transactions), 0)',
            2)]
        return line

    def _add_import(self, name):
        self.imports += ['from .{0} import {0}'.format(name)]

    def generate(self):
        self._read_file()
        return self.class_output
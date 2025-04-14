from dataclasses import dataclass
import struct
import hashlib
import numpy as np
import numpy.typing as npt

from collections.abc import Sized
from typing import Dict, Iterable, Tuple, Union
from numbers import Number

from opatio.misc.opatentity import OPATEntity


@dataclass
class CardHeader(OPATEntity):
    """
    Represents the header of a data card.

    Attributes
    ----------
    numTables : int
        Number of tables in the data card.
    indexOffset : int
        Offset to the index section.
    cardSize : int
        Size of the data card.
    comment : str
        Comment section.
    reserved : bytes
        Reserved for future use (default is 100 null bytes).
    magicNumber : str
        Magic number to validate the data card (default is "CARD").
    headerSize : int
        Size of the data card header (default is 256 bytes).
    """

    numTables: int
    indexOffset: int
    cardSize: int
    comment: str
    reserved: bytes = b"\x00"*100
    magicNumber: str = "CARD"
    headerSize: int = 256

    def set_comment(self, comment: str):
        """
        Set the comment of the data card.

        Parameters
        ----------
        comment : str
            The comment to set.

        Raises
        ------
        ValueError
            If the comment string exceeds 128 characters.

        Examples
        --------
        >>> header = CardHeader(numTables=0, indexOffset=0, cardSize=0, comment="")
        >>> header.set_comment("This is a comment.")
        """
        if len(comment) >= 128:
            raise ValueError(f"comment string ({comment}) is too long ({len(comment)}). Max length is 128")
        self.comment = comment

    def __bytes__(self) -> bytes:
        """
        Convert the card header to bytes.

        Returns
        -------
        bytes
            The card header as bytes.

        Raises
        ------
        AssertionError
            If the header size is not 256 bytes.

        Examples
        --------
        >>> header = CardHeader(numTables=1, indexOffset=256, cardSize=512, comment="Example")
        >>> bytes(header)
        """
        headerBytes = struct.pack(
            "<4s I I Q Q 128s 100s",
            self.magicNumber.encode('utf-8'),
            self.numTables,
            self.headerSize,
            self.indexOffset,
            self.cardSize,
            self.comment.encode('utf-8'),
            self.reserved
        )
        assert len(headerBytes) == 256, f"Header must be 256 bytes. Due to an unknown error the header has {len(headerBytes)} bytes"
        return headerBytes

    def __repr__(self) -> str:
        """
        Get the string representation of the card header.

        Returns
        -------
        str
            The string representation.

        Examples
        --------
        >>> header = CardHeader(numTables=1, indexOffset=256, cardSize=512, comment="Example")
        >>> repr(header)
        'CardHeader(magicNumber=CARD, numTables=1, headerSize=256, indexOffset=256, cardSize=512, comment=Example)'
        """
        return f"CardHeader(magicNumber={self.magicNumber}, numTables={self.numTables}, headerSize={self.headerSize}, indexOffset={self.indexOffset}, cardSize={self.cardSize}, comment={self.comment})"

    def ascii(self) -> str:
        """
        Get the ASCII representation of the card header.

        Returns
        -------
        str
            The ASCII representation.

        Examples
        --------
        >>> header = CardHeader(numTables=1, indexOffset=256, cardSize=512, comment="Example")
        >>> print(header.ascii())
        ========== Card Header ==========
        >> Magic Number: CARD
        >> Number of Tables: 1
        >> Header Size: 256
        >> Index Offset: 256
        >> Card Size: 512
        >> Comment: Example
        """
        asciiString = f"""========== Card Header ==========
>> Magic Number: {self.magicNumber}
>> Number of Tables: {self.numTables}
>> Header Size: {self.headerSize}
>> Index Offset: {self.indexOffset}
>> Card Size: {self.cardSize}
>> Comment: {self.comment}
"""
        return asciiString

    def copy(self):
        """
        Create a copy of the card header.

        Returns
        -------
        CardHeader
            A copy of the card header.

        Examples
        --------
        >>> header = CardHeader(numTables=1, indexOffset=256, cardSize=512, comment="Example")
        >>> header_copy = header.copy()
        >>> header_copy == header
        True
        """
        return CardHeader(
            numTables=self.numTables,
            indexOffset=self.indexOffset,
            cardSize=self.cardSize,
            comment=self.comment,
            reserved=self.reserved
        )

@dataclass
class CardIndexEntry(OPATEntity):
    """
    Represents an entry in the index of a data card.

    Attributes
    ----------
    tag : str
        Tag to identify the table.
    byteStart : int
        Byte start position of the table. These are given relative to the start
        of the card.
    byteEnd : int
        Byte end position of the table. These are given relative to the start of
        the card.
    numColumns : int
        Number of columns in the table.
    numRows : int
        Number of rows in the table.
    columnName : str
        Name of the column.
    rowName : str
        Name of the row.
    size : int
        Length of the row entry, default is 1 (scaler). Max is 2^64 - 1 (max 8 byte u int)
    reserved : bytes
        Reserved for future use (default is 12 null bytes).
    """

    tag: str
    byteStart: int
    byteEnd: int
    numColumns: int
    numRows: int
    columnName: str
    rowName: str
    size: int = 1
    reserved: bytes = b"\x00"*12

    def __bytes__(self) -> bytes:
        """
        Convert the card index to bytes.

        Returns
        -------
        bytes
            The card index as bytes.

        Raises
        ------
        AssertionError
            If the index entry size is not 64 bytes.

        Examples
        --------
        >>> index = CardIndexEntry(tag="Example", byteStart=0, byteEnd=64, numColumns=4, numRows=4, columnName="col", rowName="row")
        >>> bytes(index)
        """
        nullPaddedTag = self.tag.ljust(8, '\x00').encode('utf-8')
        nullPaddedColumnName = self.columnName.ljust(8, '\x00').encode('utf-8')
        nullPaddedRowName = self.rowName.ljust(8, '\x00').encode('utf-8')
        if not self.size.is_integer():
            raise TypeError(f"Due to an unknown error the size of the index entry is not an integer. The size is {self.size}. This is a opatio bug and should be reported.")
        indexBytes = struct.pack(
            f"<8s Q Q H H 8s 8s Q 12s",
            nullPaddedTag,
            self.byteStart,
            self.byteEnd,
            self.numColumns,
            self.numRows,
            nullPaddedColumnName,
            nullPaddedRowName,
            int(self.size),
            self.reserved
        )
        assert len(indexBytes) == 64, f"Card index entry must be 64 bytes. Due to an unknown error the card index entry has {len(indexBytes)} bytes"
        return indexBytes

    def __repr__(self) -> str:
        """
        Get the string representation of the card index.

        Returns
        -------
        str
            The string representation.

        Examples
        --------
        >>> index = CardIndexEntry(tag="Example", byteStart=0, byteEnd=64, numColumns=4, numRows=4, columnName="col", rowName="row", size=1)
        >>> repr(index)
        'CardIndexEntry(Tag=Example, byteStart=0, byteEnd=64, numColumns=4, numRows=4, columnName=col, rowName=row, size=1)'
        """
        return f"CardIndexEntry(Tag={self.tag}, byteStart={self.byteStart}, byteEnd={self.byteEnd}, numColumns={self.numColumns}, numRows={self.numRows}, columnName={self.columnName}, rowName={self.rowName}, size={self.size})"

    def ascii(self) -> str:
        """
        Get the ASCII representation of the card index.

        Returns
        -------
        str
            The ASCII representation.

        Examples
        --------
        >>> index = CardIndexEntry(tag="Example", byteStart=0, byteEnd=64, numColumns=4, numRows=4, columnName="col", rowName="row", size=1)
        >>> print(index.ascii())
        Example  |        0 |       64 |        4 |        4 | col      | row       | 1
        """
        return f"{self.tag:8} | {self.byteStart:8} | {self.byteEnd:8} | {self.numColumns:8} | {self.numRows:8} | {self.columnName:8} | {self.rowName:8} | {self.size:8}\n"

    def copy(self):
        """
        Create a copy of the card index entry.

        Returns
        -------
        CardIndexEntry
            A copy of the card index entry.

        Examples
        --------
        >>> index = CardIndexEntry(tag="Example", byteStart=0, byteEnd=64, numColumns=4, numRows=4, columnName="col", rowName="row")
        >>> index_copy = index.copy()
        >>> index_copy == index
        True
        """
        return CardIndexEntry(
            tag=self.tag,
            byteStart=self.byteStart,
            byteEnd=self.byteEnd,
            numColumns=self.numColumns,
            numRows=self.numRows,
            columnName=self.columnName,
            rowName=self.rowName,
            size = self.size,
            reserved=self.reserved
        )

class OPATCell(OPATEntity):
    data : npt.ArrayLike
    shape: Tuple[int, ...]

    def __init__(self, data):
       try:
           self.build(data)
       except Exception as e:
           raise Exception(f"An unknown error occurred while building the OPAT entity: {e}")

    def from_ndarray(self, ndarray: npt.ArrayLike):
        if not isinstance(ndarray, np.ndarray):
            raise TypeError(f"ndarray must be a numpy array! Currently it is {type(ndarray)}")
        self.shape = ndarray.shape
        self.data = ndarray

    def build(self, data):
        if isinstance(data, npt.ArrayLike):
            self.from_ndarray(data)
        else:
            try:
                data = np.array(data)
                if data.dtype.kind not in {'i', 'f', 'u'}:
                    raise TypeError(f"Unsupported data type: {data.dtype}")
                self.from_ndarray(data)
            except TypeError as e:
                raise TypeError(f"Data must be castable to a numeric numpy array! Currently it is {type(data)}. {e}")
            except ValueError as e:
                raise ValueError(f"Data must be castable to a numeric numpy array! Currently it is {type(data)}. {e}")
            except Exception as e:
                raise Exception(f"An unknown error occurred while building the OPAT entity: {e}")

    def __bytes__(self) -> bytes:
        """
        recurse through the entire entity and convert it to a flat byte stream.

        Returns
        -------
        bytes
            The OPAT entity as bytes.
        """
        return self.data.flatten().tobytes()

    def __repr__(self) -> str:
        """
        Get the string representation of the OPAT entity.

        Returns
        -------
        str
            The string representation.
        """
        if self.data.ndim == 1 and self.data.shape[0] == 1:
            return str(self.data[0])
        else:
            return ', '.join([str(x) for x in self.data.flatten()])

    def ascii(self) -> str:
        return self.__repr__()

    def __array__(self, dtype=None):
        if dtype.kind not in {'i', 'f', 'u'}:
            raise TypeError(f"Unsupported data type: {dtype}")
        return self.data.flatten()

@dataclass
class OPATTable(OPATEntity):
    """
    Structure to hold the data of a single table. Recall the structure of an OPAT file
    is a collection of data cards, each containing a header, an index, and a collection
    of tables. Each table is represented by this class.

    Notes
    -----
    - Generally, the user should not need to create an OPATTable directly. Instead,
    opatio will use these internally. However, this class is provided for
    completeness and for any advanced users who may want to create their own
    tables.


    Attributes
    ----------
    columnValues : Iterable[float]
        Column values of the table.
    rowValues : Iterable[float]
        Row values of the table.
    data : npt.ArrayLike
        Data of the table.

    Examples
    --------
    >>> import numpy as np
    >>> table = OPATTable(columnValues=np.array([1.0, 2.0]), rowValues=np.array([3.0, 4.0]), data=[[5.0, 6.0], [7.0, 8.0]])
    """

    columnValues: npt.ArrayLike
    rowValues: npt.ArrayLike
    data: npt.ArrayLike
    _size: int = ...

    def __post_init__(self):
        if self.data.ndim != 2 and self.data.ndim != 3:
           raise ValueError(f"data must be a 2D or 3D array! Currently it is {self.data.ndim}D")

        if self.data.ndim == 2:
            self._size = 1
        elif self.data.ndim == 3:
            self._size = self.data.shape[2]

    @property
    def size(self) -> int:
        return self._size

    def sha256(self) -> "_Hash":
        """
        Compute the SHA-256 checksum of the given data.

        Returns
        -------
        bytes
            The SHA-256 checksum.

        Raises
        ------
        ValueError
            If the data cannot be cast to a numpy array.

        Examples
        --------
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> table.sha256()
        """
        flatData = self.data.flatten()
        return hashlib.sha256(flatData.tobytes())

    def __bytes__(self) -> bytes:
        """
        Convert the single OPAT format table to bytes.

        Returns
        -------
        bytes
            The OPAT table as bytes.

        Raises
        ------
        ValueError
            If columnValues, rowValues, or data cannot be cast to numpy arrays.

        AssertionError
            If the byte sizes of columnValues, rowValues, or data are incorrect.

        Examples
        --------
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> bytes(table)
        """
        if not isinstance(self.columnValues, np.ndarray):
            try:
                cV = np.array(self.columnValues, dtype=np.float64).flatten()
            except ValueError as e:
                raise ValueError(f"columnValues must be castable to a numpy array! Currently it is {type(self.columnValues)}. {e}")
        else:
            cV = self.columnValues.flatten()
        if not isinstance(self.rowValues, np.ndarray):
            try:
                rV = np.array(self.rowValues, dtype=np.float64).flatten()
            except ValueError as e:
                raise ValueError(f"rowValues must be castable to a numpy array! Currently it is {type(self.rowValues)}. {e}")
        else:
            rV = self.rowValues.flatten()
        if not isinstance(self.data, np.ndarray):
            try:
                data = np.array(self.data, dtype=np.float64).flatten()
            except ValueError as e:
                raise ValueError(f"data must be castable to a numpy array! Currently it is {type(self.data)}. {e}")
        else:
            data = self.data.flatten()

        tableBytes = struct.pack(
            f"<{len(rV)}d{len(cV)}d{len(data)}d",
            *cV,
            *rV,
            *data
        )
        return tableBytes


    @staticmethod
    def compute_col_width(size: int, floatWidth: int) -> int:
        """
        Computes the total width of a cell that will hold `size` floats,
        each with `floatWidth` characters, formatted like <f1, f2, ..., fN>.
        """
        # Width per float plus the separator ", "
        floatWidth = len(f"{0:7.{floatWidth}f}")
        perFloat = floatWidth
        separatorWidth = 2 * (size - 1) if size > 1 else 0
        # Include 2 for the surrounding <>
        bracketWidth = 2 if size > 1 else 0
        return int(size * perFloat + separatorWidth + bracketWidth)

    def format_centered(self, value: float, floatWidth: int) -> str:
        """
        Centers a single float value in a fixed-width field.
        """
        totalWidth = self.compute_col_width(self.size, floatWidth)
        formatSpec = f"^{totalWidth}.{floatWidth}f"
        return f"{value:{formatSpec}}"

    def ascii(self) -> str:
        """
        Get the ASCII representation of the OPAT table.

        Returns
        -------
        str
            The ASCII representation.

        Examples
        --------
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> print(table.ascii())
        """
        tableStr = ""
        numRows = len(self.rowValues)
        numColumns = len(self.columnValues)
        # colNameRow = " | ".join([f"{col:4.4f}" for col in self.columnValues])
        colNameRow = " | ".join([self.format_centered(col, 4) for col in self.columnValues])
        colNameRow = "        | " + colNameRow
        tableStr += colNameRow + "\n"
        tableStr += "-" * (len(colNameRow) + 4) + "\n"
        for i in range(numRows):
            cellValues = [self.data[i][j] for j in range(numColumns)]
            if isinstance(cellValues[0], np.ndarray):
                dataSequence = [', '.join([f"{y:7.4f}" for y in x]) for x in cellValues]
                dataVectorFormated = [f'<{x}>' if ',' in x else x for x in dataSequence]
            else:
                dataVectorFormated = [f"{x:7.4f}" for x in cellValues]

            row = " | ".join(dataVectorFormated)
            tableStr += f"{self.rowValues[i]:7.4f} | " + row + "\n"
        return tableStr

    def copy(self):
        """
        Create a copy of the OPAT table.

        Returns
        -------
        OPATTable
            A copy of the OPAT table.

        Examples
        --------
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> table_copy = table.copy()
        >>> table_copy == table
        True
        """
        newTable = OPATTable(
            columnValues=self.columnValues.copy(),
            rowValues=self.rowValues.copy(),
            data=self.data.copy()
        )
        return newTable

@dataclass
class DataCard(OPATEntity):
    """
    Represents a data card containing header, index, and tables.

    Attributes
    ----------
    header : CardHeader
        Header of the data card.
    index : Dict[str, CardIndexEntry]
        Index of the data card.
    tables : Dict[str, OPATTable]
        Tables in the data card.

    Methods
    -------
    add_table(tag: str, table: OPATTable, columnName: str = "columnValues", rowName: str = "rowValues")
        Add a table to the data card.

    sha256() -> bytes
        Compute the SHA-256 hash of the data card. Note that this is the combination hash of
        all the tables in the card including their data, column values, and row values.

    ascii() -> str
        Get the ASCII representation of the data card.

    copy() -> DataCard
        Create a copy of the data card.

    Examples
    --------
    >>> card = DataCard()
    >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
    >>> card.add_table(tag="Example", table=table)
    """

    header: CardHeader
    index: Dict[str, CardIndexEntry]
    tables: Dict[str, OPATTable]

    def __init__(self):
        """
        Initialize a DataCard instance.
        """
        self.header = CardHeader(numTables=0, indexOffset=256, cardSize=256, comment="")
        self.index = {}
        self.tables = {}

    def add_table(self, tag: str, table: OPATTable, columnName: str = "columnValues", rowName: str = "rowValues"):
        """
        Add a table to the data card.

        Parameters
        ----------
        tag : str
            Tag to identify the table.
        table : OPATTable
            The table to add.
        columnName : str, optional
            Name of the column (default is "columnValues").
        rowName : str, optional
            Name of the row (default is "rowValues").

        Raises
        ------
        TypeError
            If table is not an OPATTable or tag is not a string.
        ValueError
            If a table with the same tag already exists.

        Examples
        --------
        >>> card = DataCard()
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> card.add_table(tag="Example", table=table)
        """
        if not isinstance(table, OPATTable):
            raise TypeError(f"table must be an OPATTable! Currently it is {type(table)}")

        if not isinstance(tag, str):
            raise TypeError(f"tag must be a string! Currently it is {type(tag)}")

        if tag in self.index:
            raise ValueError(f"Table with tag {tag} already exists in the card!")

        # Add the table to the data card
        self.tables[tag] = table

        byteStart = max([entry.byteEnd for entry in self.index.values()], default=256)

        # Create the index entry for the table
        index = CardIndexEntry(
            tag=tag,
            byteStart=byteStart,
            byteEnd=byteStart + len(table),
            numColumns=len(table.columnValues),
            numRows=len(table.rowValues),
            columnName=columnName,
            rowName=rowName,
            size=table.size
        )

        # Add the index entry to the data card
        self.index[tag] = index

        # Update the header information
        self.header.numTables += 1
        cardSize = 256
        indexOffset = 256
        for tag in self.tables:
            cardSize += len(self.tables[tag])
            cardSize += len(self.index[tag])
            indexOffset += len(self.tables[tag])
        self.header.cardSize = cardSize
        self.header.indexOffset = indexOffset

    def sha256(self) -> bytes:
        """
        Compute the SHA-256 hash of the data card.

        Returns
        -------
        bytes
            The SHA-256 hash of the data card.

        Examples
        --------
        >>> card = DataCard()
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> card.add_table(tag="Example", table=table)
        >>> card.sha256()
        """
        sha256 = hashlib.sha256()
        for _, table in self.tables.items():
            sha256.update(table.sha256().digest())

        return sha256.digest()

    def __bytes__(self) -> bytes:
        """
        Convert the data card to bytes.

        Returns
        -------
        bytes
            The data card as bytes.

        Examples
        --------
        >>> card = DataCard()
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> card.add_table(tag="Example", table=table)
        >>> bytes(card)
        """
        headerBytes = bytes(self.header)
        indexBytes = b"".join(bytes(index) for _, index in self.index.items())
        tablesBytes = b"".join(bytes(table) for _, table in self.tables.items())
        return headerBytes + tablesBytes + indexBytes

    def __getitem__(self, key: str) -> OPATTable:
        """
        Get the table by index.

        Parameters
        ----------
        key : str
            The index of the table.

        Returns
        -------
        OPATTable
            The table.

        Raises
        ------
        TypeError
            If key is not a string.
        KeyError
            If the table with the given index is not found.

        Examples
        --------
        >>> card = DataCard()
        >>> table = OPATTable(columnValues=[1.0, 2.0], rowValues=[3.0, 4.0], data=[[5.0, 6.0], [7.0, 8.0]])
        >>> card.add_table(tag="Example", table=table)
        >>> card["Example"]
        """
        if not isinstance(key, str):
            raise TypeError(f"key must be a string! Currently it is {type(key)}")
        if key not in self.index:
            raise KeyError(f"Table with index {key} not found.")
        return self.tables[key].copy()

    def __repr__(self) -> str:
        """
        Get the string representation of the data card.

        Returns
        -------
        str
            The string representation.

        Examples
        --------
        >>> card = DataCard()
        >>> repr(card)
        'DataCard(numTables=0, indexOffset=256, cardSize=256, comment=)'
        """
        reprString = f"""DataCard(numTables={self.header.numTables}, indexOffset={self.header.indexOffset}, cardSize={len(self)}, comment={self.header.comment})"""
        return reprString

    def ascii(self) -> str:
        """
        Get the ASCII representation of the data card.

        Returns
        -------
        str
            The ASCII representation.

        Examples
        --------
        >>> card = DataCard()
        >>> print(card.ascii())
        """
        asciiRepr = "======== START Data Card ========\n"
        asciiRepr += self.header.ascii()

        asciiRepr += "======== Tables ========\n"
        for i, (tag, table) in enumerate(self.tables.items()):
            index = self.index[tag]
            asciiRepr += f"-------- Table {i} (tag: {index.tag}) --------\n"
            asciiRepr += table.ascii()

        asciiRepr += "======== Card Index ========\n"
        for tag, index in self.index.items():
            asciiRepr += index.ascii()

        asciiRepr += "========= END Data Card =========\n"
        return asciiRepr

    def copy(self):
        """
        Create a copy of the data card.

        Returns
        -------
        DataCard
            A copy of the data card.

        Examples
        --------
        >>> card = DataCard()
        >>> card_copy = card.copy()
        >>> card_copy == card
        True
        """
        newCard = DataCard()
        newCard.header = self.header.copy()
        newCard.index = {tag: index.copy() for tag, index in self.index.items()}
        newCard.tables = {tag: table.copy() for tag, table in self.tables.items()}
        return newCard

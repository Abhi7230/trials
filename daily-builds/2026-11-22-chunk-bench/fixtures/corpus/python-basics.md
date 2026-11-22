# Python Programming Basics

## Introduction to Python

Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum and first released in 1991, Python emphasizes code readability with significant use of whitespace.

## Data Types

### Numbers

Python supports integers, floats, and complex numbers. Integers can be of any length and are written without decimal points.

```python
x = 42
y = 3.14
z = 1 + 2j
```

### Strings

Strings in Python are sequences of characters enclosed in quotes. You can use single, double, or triple quotes.

```python
text = "Hello, World!"
multiline = """This is
a multiline string"""
```

## Control Flow

### If Statements

Conditional statements allow you to execute code based on conditions:

```python
if x > 0:
    print("Positive")
elif x < 0:
    print("Negative")
else:
    print("Zero")
```

### Loops

Python provides for and while loops for iteration:

```python
for i in range(5):
    print(i)

while x > 0:
    x -= 1
```

## Functions

Functions are defined using the def keyword and can accept parameters and return values.

```python
def greet(name):
    return f"Hello, {name}!"
```

## Lists and Dictionaries

Lists are ordered collections and dictionaries store key-value pairs. Both are fundamental data structures in Python.

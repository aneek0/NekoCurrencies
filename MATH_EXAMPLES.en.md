# 🧮 Mathematical Expressions in Currency Converter Bot

The bot supports computing simple mathematical expressions with automatic currency detection.

## ✨ Supported Operations

- **Addition**: `+`
- **Subtraction**: `-`
- **Multiplication**: `*` or `×`
- **Division**: `/` or `÷`
- **Parentheses**: `()` for operation grouping

## 💡 Usage Examples

### 🟢 Simple Expressions

```
Input: "10 + 20 dollars"
Output: $30

Input: "100 - 25 rubles"
Output: ₽75

Input: "50 * 2 tenge"
Output: ₸100

Input: "1000 / 4 euros"
Output: €250
```

### 🟡 Expressions with Parentheses

```
Input: "(20 + 5) * 4 dollars"
Output: $100

Input: "(100 + 50) / 3 EUR"
Output: $50

Input: "(15 + 5) / 2 USD"
Output: $10

Input: "(1000 - 100) / 3 rubles"
Output: ₽300
```

### 🔵 Complex Expressions

```
Input: "100 + 200 + 300 hryvnias"
Output: ₴600

Input: "1000 - 100 - 50 BYN"
Output: 850 BYN

Input: "5 * 10 * 2 dollars"
Output: $100

Input: "100 + 50 * 2 euros"
Output: €200
```

### 🟣 Different Currency Formats

```
Input: "(20 + 5) * 4$"
Output: $100

Input: "10 + 20€"
Output: €30

Input: "100 - 25₽"
Output: ₽75

Input: "50 * 2₸"
Output: ₸100

Input: "(15 + 5) / 2 USD"
Output: $10

Input: "100 + 200 + 300 RUB"
Output: 600 RUB
```

## 🚫 Limitations

- Only basic mathematical operations are supported
- Maximum complexity: 3-4 operations
- Functions (sin, cos, log, etc.) are not supported
- Powers and roots are not supported
- Standard operator precedence (multiplication/division before addition/subtraction)

## 💻 Technical Details

- Expressions are computed using safe `eval()`
- Result is rounded to 2 decimal places
- Decimal numbers with dot and comma are supported
- Automatic currency detection from text
- Fallback to standard currency recognition

## 🔍 How It Works

1. **Parsing**: Bot analyzes text for mathematical expressions
2. **Currency Extraction**: Determines currency from text (symbols, codes, names)
3. **Computation**: Safely computes mathematical expression
4. **Formatting**: Formats result with correct currency symbol
5. **Conversion**: Converts to other currencies if needed

## 🎯 Best Practices

- Use parentheses for explicit operation order
- Place currency at the end of expression for better recognition
- Use standard operator symbols (+, -, *, /)
- Break complex calculations into simple expressions 
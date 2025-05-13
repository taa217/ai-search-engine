# Save this as clean_null_bytes.py in the same directory as search_tools.py
with open('src/utils/search_tools.py', 'rb') as f:
    data = f.read()
cleaned = data.replace(b'\x00', b'')
with open('src/utils/search_tools.py', 'wb') as f:
    f.write(cleaned)
print("Null bytes removed.")
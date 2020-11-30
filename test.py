# coding=utf-8

if __name__ == "__main__":
    f = '\u53eb\u6211'
    print f
    print f.decode('unicode-escape')
    print f.encode('utf-8')
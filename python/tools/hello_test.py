print("HELLO_TEST_SCRIPT: Hello from hello_test.py!")
try:
    with open("/a0/tmp/hello_test_output.txt", "w") as f:
        f.write("Hello test script was executed.\n")
    print("HELLO_TEST_SCRIPT: Successfully wrote to /a0/tmp/hello_test_output.txt")
except Exception as e:
    print(f"HELLO_TEST_SCRIPT: Error writing to file: {e}")
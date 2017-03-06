Unfortunately there are not test scripts in this folder. Writing automatic test is complicated and will spend a lot of time, although it's worth to do.

However, there are some test data in the `fixtures/` folder. They can be used to do manual test with `nc`.

For example, setup a mock server with fixed response:

    ```
    nc -l 4567 < fixtures/chunked_response.txt
    ```

Or send a particular request to `socks2http` server:

    ```
    nc 127.0.0.1 1234 < fixtures/chunked_post.txt
    ```

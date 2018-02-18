## SnakeParse using `argparse` and a custom method named snakeparser 

To execute this example, run:

```snakeparse --snakefile-globs examples/argparse/*.smk -- WriteMessage --message "Hello World!"```
where your message ("Hello World!") should be written to `message.txt`.

or

```snakeparse --snakefile-globs examples/argparse/*.smk -- WriteLog --message "Log it!"```
where your message ("Log it!") should be written to `log.txt`.


import os
import subprocess
import sys

from backend.config import settings

def main():
    database_url = settings.test_database_url

    if database_url.rsplit('/', 1)[-1] != 'emporio_test':
        raise RuntimeError('Tests must use emporio_test')

    env = os.environ.copy()
    env['DATABASE_URL'] = database_url

    subprocess.run([sys.executable, '-m', 'tortoise', 'migrate'], env=env, check=True)
    subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-v'], env=env, check=True)

if __name__ == '__main__':
    main()
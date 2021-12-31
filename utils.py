from threading import Lock
import logging

g_Lock = Lock()

def write_config(filename, filecontent):
    '''Write config file.'''

    logging.debug("rEescrevendo o arquivo %s", filename)
    g_Lock.acquire()

    try:
        with open(filename, 'w') as f:
            f.write(filecontent)

    except Exception as e:
        logging.warning("Falha ao escrever o arquivo %s: %s", filename, e)

    finally:
        g_Lock.release()

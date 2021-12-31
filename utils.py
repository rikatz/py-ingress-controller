from threading import Lock
import logging

g_Lock = Lock() 

def write_config(filename, filecontent):
    logging.debug("escrevendo o arquivo %s", filename)
    g_Lock.acquire()
    try: 
        f = open(filename, "w")
        f.write(filecontent)
    except Exception as e:
        logging.warning("Falha ao escrever o arquivo %s: %s", filename, e)
    finally:
        f.close()
        g_Lock.release()


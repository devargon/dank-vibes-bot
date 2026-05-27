import os

server_id = 1200400184748802168 if "preproduction" in os.getenv("APPEALS_SERVER_HOST") else 1288032530569625660 if "banappeal." in os.getenv("APPEALS_SERVER_HOST") else 871734809154707467
banappeal_chn_id = 1200705116857176135 if "preproduction" in os.getenv("APPEALS_SERVER_HOST") else 1345459131204505691 if "banappeal." in os.getenv("APPEALS_SERVER_HOST") else 1194673636196491396
modlog_chn_id = 1200707746622869535 if "preproduction" in os.getenv("APPEALS_SERVER_HOST") else 1317868064469028874 if "banappeal." in os.getenv("APPEALS_SERVER_HOST") else 999661054067998720
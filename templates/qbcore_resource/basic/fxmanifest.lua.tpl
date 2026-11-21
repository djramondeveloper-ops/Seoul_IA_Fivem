fx_version 'cerulean'
game 'gta5'

lua54 'yes'

name '{{RESOURCE_NAME}}'
author 'mz_fivem_agent'
description 'Resource {{RESOURCE_NAME}} gerado automaticamente'
version '1.0.0'

shared_scripts {
    'shared/config.lua'
}

client_scripts {
    'client/main.lua'
}

server_scripts {
    'server/main.lua'
}

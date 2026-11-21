fx_version 'cerulean'
game 'gta5'

lua54 'yes'

name '{{RESOURCE_NAME}}'
author 'mz_fivem_agent'
description 'Resource {{RESOURCE_NAME}} com NUI gerado automaticamente'
version '1.0.0'

ui_page 'web/index.html'

files {
    'web/index.html',
    'web/style.css',
    'web/app.js'
}

shared_scripts {
    'shared/config.lua'
}

client_scripts {
    'client/main.lua'
}

server_scripts {
    'server/main.lua'
}

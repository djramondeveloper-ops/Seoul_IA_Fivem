RegisterCommand('{{RESOURCE_NAME}}', function()
    SetNuiFocus(true, true)
    SendNUIMessage({
        action = 'open',
        resource = Config.ResourceName,
    })
end, false)

RegisterNUICallback('close', function(_, cb)
    SetNuiFocus(false, false)
    cb({ ok = true })
end)

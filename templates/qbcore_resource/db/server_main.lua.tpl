CreateThread(function()
    if Config.Debug then
        print(('[%s] server iniciado com banco %s'):format(Config.ResourceName, Config.Database))
    end
end)

require(["gitbook"], function(gitbook) {
    // plugin config
    // var config;

    // function createAdElement(adConfig) {
    //     adElement = document.createElement('ins');
    //     adElement.style = 'display: block';
    //     adElement.className = 'adsbygoogle';
    //     adElement.setAttribute('data-ad-client', adConfig.client);
    //     adElement.setAttribute('data-ad-slot', adConfig.slot);
    //     adConfig.format && adElement.setAttribute('data-ad-format', adConfig.format);
    //     adConfig.style && adElement.setAttribute('style', adConfig.style);

    //     return adElement;
    // }

    // function injectAds(configs) {
    //     if(configs && configs.length > 0) {
    //         configs.forEach(function(c) {
    //             document.querySelector(c.location).appendChild(createAdElement(c));
    //             (adsbygoogle = window.adsbygoogle || []).push({});
    //         });
    //     }
    // }

    gitbook.events.bind("start", function(e, pluginConfig) {
        // console.log("=================== google-adsense start: pluginConfig=%o", pluginConfig);
        configs = pluginConfig['google-adsense'].ads;
        // console.log("configs=%o", configs);
        firstConfig = configs[0]
        firstClient = firstConfig.client
        // console.log("firstClient=%o", firstClient);

        // init script
        var adScript = document.createElement('script');
        // adScript.src = '//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';
        adScript.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';
        adScript.setAttribute('async', true);
        adScript.setAttribute('data-ad-client', firstClient); // add for Google Adsense Auto Ads
        console.log("adScript=%o", adScript);
        document.body.appendChild(adScript);
    });

    // gitbook.events.bind("page.change", function() {
    //     if (config) {
    //         injectAds(config);
    //     }
    // });
});

window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                classes,
                colors,
                colorProp
            } = context.hideout;
            const v = feature.properties[colorProp];
            if (v === null || v === undefined || isNaN(v)) {
                return {
                    fillColor: '#cccccc',
                    color: '#222',
                    weight: 1,
                    fillOpacity: 0.4
                };
            }
            for (let i = 0; i < classes.length; i++) {
                if (v <= classes[i]) {
                    return {
                        fillColor: colors[i],
                        color: '#222',
                        weight: 1,
                        fillOpacity: 0.7
                    };
                }
            }
            return {
                fillColor: colors[colors.length - 1],
                color: '#222',
                weight: 1,
                fillOpacity: 0.7
            };
        }
    }
});
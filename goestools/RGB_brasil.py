import goes
import os.path
import numpy as np
from mpl_toolkits.basemap import Basemap
import pandas as pd
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt

extent=[-75, -35.0, -33, 6]
#extent=[-75, -35, -33, -20]
#extent=[-85, 20, -75, 30]

dates = [date.strftime('%Y%m%d%H%M') for date in pd.date_range('201804091200','201804091900', freq='15min')]

for date in dates:
    if not os.path.isfile('/home/josue/goes_imgs/'+ date +'.png'):
        data = goes.goes(16, 'CMIP', 'F', date=date, bands=[1,2,3], path='../data/', extent=extent, local=False)
        data.rgb_truecolor()
        #plt.figure()
        #plt.imshow(np.power(data.RGB.data,0.5))
        #data.C01 = data.C01.four_elements_avg()
        #plt.figure()
        #plt.imshow(data.C01.data)
        
        #plt.figure()
        #plt.imshow(np.power(data.C13.data,0.7))
        
        plt.ioff()
        
        dpi = 93
        height, width, _ = data.RGB.data.data.shape
        figsize = width / float(dpi), height / float(dpi)
        ax = plt.figure(figsize=figsize)
        
        bmap = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[1], urcrnrlon=extent[2], urcrnrlat=extent[3], epsg=4326)
        bmap.imshow(data.RGB.data.data, origin='upper')
        #bmap.readshapefile('../resources/ne_10m_admin_0_countries/ne_10m_admin_0_countries', 'ne_10m_admin_0_countries', linewidth=3, color='grey')
        bmap.readshapefile('../resources/ne_50m_admin_1_states_provinces/ne_50m_admin_1_states_provinces', 'ne_50m_admin_1_states_provinces', linewidth=3, color='black')
        
        # Draw parallels and meridians
        #bmap.drawparallels(np.arange(-90.0, 90.0, 5.0), linewidth=0.2, dashes=[4, 4], color='white', labels=[False, False, False, False], fmt='%g', labelstyle="+/-", xoffset=-0.80, yoffset=-1.00, size=7)
        #bmap.drawmeridians(np.arange(0.0, 360.0, 5.0), linewidth=0.2, dashes=[4, 4], color='white', labels=[False, False, False, False], fmt='%g', labelstyle="+/-", xoffset=-0.80, yoffset=-1.00, size=7)
        
        ax.savefig('/home/josue/goes_imgs/'+ date +'.png',bbox_inches='tight', pad_inches = 0, dpi=dpi)

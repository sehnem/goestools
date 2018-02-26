import goes
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap

# TODO = Arrumar os atributos do xarray para uma reprojeção correta

extent=[-58, -35.0, -48, -25.0]
#extent=[-100.7844079, 15, -66.9513812, 35] #conus
#'201802231730'
data = goes.goes(16, 'CMIP', 'F', '201802241600', bands=[1,2,3], path='../data/', extent=extent, local=False)
data.rgb_truecolor()
#plt.figure()
#plt.imshow(np.power(data.RGB.data,0.5))
#data.C01 = data.C01.four_elements_avg()
#plt.figure()
#plt.imshow(data.C01.data)

plt.figure()
plt.imshow(np.power(data.C02.data,0.7))

dpi = 150
height, width, _ = data.RGB.data.data.shape
figsize = width / float(dpi), height / float(dpi)
ax = plt.figure(figsize=figsize)

bmap = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[1], urcrnrlon=extent[2], urcrnrlat=extent[3], epsg=4326)
bmap.imshow(np.power(data.RGB.data.data,0.5), origin='upper')
bmap.readshapefile('../resources/ne_10m_admin_0_countries', 'ne_10m_admin_0_countries', linewidth=0.6, color='black')

# Draw parallels and meridians
bmap.drawparallels(np.arange(-90.0, 90.0, 5.0), linewidth=0.2, dashes=[4, 4], color='white',
                   labels=[False, False, False, False], fmt='%g', labelstyle="+/-", xoffset=-0.80, yoffset=-1.00,
                   size=7)
bmap.drawmeridians(np.arange(0.0, 360.0, 5.0), linewidth=0.2, dashes=[4, 4], color='white',
                   labels=[False, False, False, False], fmt='%g', labelstyle="+/-", xoffset=-0.80, yoffset=-1.00,
                   size=7)

ax.savefig('/home/josue/teste.png',bbox_inches='tight', pad_inches = 0, dpi=dpi)

// Authored Gecko entries are scoped to an exact disc target, independently of progress reports.
export const geckoCodes = {
  n100f: {
    'GIHE78-rev0': [
      {
        id:'ultrawide-21-9', title:'21:9 Ultrawide Fix', description:'',
        notes:"Widens the game's 4:3 view to 21:9, so objects at the edges of the screen don't get culled. This code is for 21:9 only; on 16:9, use a 16:9 widescreen code instead. Turn off Dolphin's widescreen hack and set the aspect ratio to Stretch.",
        rawIni:`[Gecko]
$21:9 Ultrawide Fix [mits]
06003700 0000001C
3d808000 c00c3718
ec010032 d0010008
fc400818 48003c94
3fe55555 00000000
040073a4 4280c35c
040073bc 60000000
`
      },
      {
        id:'infinite-health', title:'Infinite Health', description:'',
        notes:"Turns on the developers' own invincibility switch, a leftover setting from the game's config file. You won't lose health, and water won't drown you. You still get knocked back, and falls still kill you.",
        rawIni:`[Gecko]
$Infinite Health [mits]
04235304 00000000
`
      },
      {
        id:'pickup-reach-fix', title:'Pickup Reach Fix', description:'',
        notes:"Fixes an original bug where Scooby's head can't collect pickups. The game checks his head at body height, so items above him pass right through it. With the fix, overhead items that were hard to reach, or that he'd phase through, now collect accurately.",
        rawIni:`[Gecko]
$Pickup Reach Fix [mits]
C204DB58 00000003
C0C4069C C0A30034
ECC62828 ECC601B2
EC00302A 00000000
`
      },
      {
        id:'restored-enemy-drops', title:'Restored Enemy Drops', description:'',
        notes:"Restores a cut projectile system that made enemies throw out items when they die. The developers wired gum, soap, food and snacks to enemies but never finished the code, so nothing came out. This code finishes it and replaces the game's random drops.",
        rawIni:`[Gecko]
$Restored Enemy Drops [mits]
040BDE88 38000000
C20BDADC 00000004
88070004 819E0010
558C0080 28000004
40820008 658C4000
919E0010 00000000
C20BD5F8 00000032
9421FFD0 7C0802A6
90010034 90610008
9081000C 90A10010
2C040002 40820150
80C300F4 2C060000
41820144 80C60080
2C060000 41820138
80E60060 2C070003
4180012C 2C070006
41810124 81030118
2C080000 41800118
2C070006 40820014
814300F4 814A0010
754A4000 40820100
3D003E99 6108999A
91010014 C0410014
C0030104 FC001040
418000E4 8103002C
81080020 3D208023
61294AE0 C0680030
C0890244 EC632028
ECA300F2 C0680034
C0890248 EC632028
ECA328FA C0680038
C089024C EC632028
ECA328FA 3D004010
91010014 C0410014
FC051040 41810090
3D00BF80 91030118
2C070006 4082001C
38600001 3D808005
618CA374 7D8903A6
4E800421 48000068
2C070005 40820024
816905C4 396B0005
818905CC 7C0B6000
40810008 7D8B6378
916905C4 48000040
2C070004 40820024
816905C0 396B0005
818905C8 7C0B6000
40810008 7D8B6378
916905C0 48000018
38600001 3D808005
618CA2A0 7D8903A6
4E800421 80610008
8081000C 80A10010
80010034 7C0803A6
38210030 9421FFE0
60000000 00000000
0407BC1C 4E800020
`
      }
    ]
  }
};

// Site-owned editorial content. Measurements, target identity and artwork remain in decomp-data.
// Bios support plain text with *emphasis* only. Codes are opt-in per explicit target.
const games = {
  n100f: {
    developer:'Heavy Iron Studios', publisher:'THQ', genre:'Action adventure',
    paragraphs:[
    'Most dogs will sit for a treat. In *Scooby-Doo! Night of 100 Frights*, one has apparently agreed to clear an entire haunted estate for a box of biscuits. Somebody get this Great Dane a union representative!',
    'Heavy Iron Studios understood exactly what made the original cartoon work. Between its familiar monsters, elaborate contraptions, timely laugh tracks, and deeply questionable property management, the game feels like a Hanna-Barbera episode you can wander around inside.',
    'There is something particularly charming about this era of licensed platformers. Every recognizable sound effect and ridiculous animation feels like somebody cared, even if the gameplay is a little rough around the edges. But those same imperfections still drive an avid speedrunning community to this day, even far beyond their days of being a meddling kid.',
    'Join me as we reverse engineer haunted real estate, suspicious collision boxes, and the precise quantity of C++ required to make a talking dog afraid of an unemployed man in a rubber mask.'
  ]
  },
  tw2004: {
    developer:'EA Redwood Shores', publisher:'EA Sports', genre:'Golf',
    paragraphs:[
      "While nothing can truly stop Father Time, *Tiger Woods PGA Tour 2004* captures an era unburdened by infamous DUIs and a bum back.",
      "All joking aside, EA Redwood Shores showed the entire industry that sports titles didn’t need to take themselves so seriously. Striking an immaculate balance between grounded simulation and pure arcade flair, this early 2000s engine delivered far more than a routine virtual round of 18. Nothing since has quite replicated the distinct rush of sinking a 20-foot eagle putt followed immediately by a gymnastic breakdancing celebration.",
      "While the 2002–2005 window was the golden age for this engine, Redwood Shores perfected the formula in 2004. Between the debut of GameFace, a massive 19-course roster (14 licensed, 5 fantasy), and a revamped World Tour Tiger Challenge, it earned the franchise's highest critical acclaim. Even though I spent nearly my entire childhood glued to the 2003 edition, 2004 preserves every ounce of that charm while layering in crucial quality-of-life upgrades. It is the rare sequel that managed to completely dethrone my own childhood nostalgia for the top spot.",
      "Join me as we reverse engineer famous PGA layouts, simulated ball physics, and slightly derivative (even borderline racist) caricature opponents."
    ]
  },
  mvp2005: {developer:'EA Canada', publisher:'EA Sports', genre:'Baseball'},
  nflstreet2: {developer:'EA Tiburon', publisher:'EA Sports BIG', genre:'American football'}
};

/** Resolve editorial content for this game and target without changing report capabilities.
 * New games need no editorial record to render; missing bios are omitted, never placeholders.
 * @param {{slug:string,console?:string,year?:string,selectedTarget?:{id:string,region:string}}} project
 */
export function gameEditorial(project) {
  const content=games[project.slug]||{};
  return {
    paragraphs:content.paragraphs||[],
    facts:[['Developer',content.developer],['Publisher',content.publisher],['Released',project.year],
      ['Genre',content.genre],['Console',project.console],['Region',project.selectedTarget?.region]].filter(([,value])=>value),
    codes:content.codes?.[project.selectedTarget?.id]||[],
  };
}

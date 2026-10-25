import {reportProjects} from './report-projects.js';
export const projects=Object.values(reportProjects).map(project=>({
  ...project,shortTitle:project.shortTitle||project.title,
  href:`/games/${project.slug}/`,repo:`https://github.com/${project.repository}`,
  cover:project.artwork.cover,coverWidth:project.artwork.width,coverHeight:project.artwork.height
}));

export async function fetchSummary(project, signal) {
  const read = async url => {
    const response = await fetch(url, {signal, cache:'no-cache'});
    if (!response.ok) throw Error('Report unavailable');
    return response.json();
  };
  const [summary, latest] = await Promise.all([
    read(project.summaryUrl),
    project.latestCommit || null
  ]);
  return latest ? {...summary, latest_commit:latest} : summary;
}

import StatsPanel from './components/StatsPanel';
import DataExport from './components/DataExport';
import './Stats.css';

interface StatsProps {
  characterId: number;
  characterName: string;
}

export default function Stats({ characterId, characterName }: StatsProps) {
  return (
    <div className="stats-page">
      <StatsPanel characterId={characterId} />
      <DataExport characterId={characterId} characterName={characterName} />
    </div>
  );
}
import StatsPanel from './components/StatsPanel';
import './Stats.css';

interface StatsProps {
  characterId: number;
}

export default function Stats({ characterId }: StatsProps) {
  return (
    <div className="stats-page">
      <StatsPanel characterId={characterId} />
    </div>
  );
}
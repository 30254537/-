import { useEffect } from "react";
import { useApp } from "./store";
import { Sidebar } from "./components/Sidebar";
import { Player } from "./components/Player";
import { Dashboard } from "./views/Dashboard";
import { Library } from "./views/Library";
import { Recommend } from "./views/Recommend";
import { PlaylistBuilder } from "./views/PlaylistBuilder";
import { Dedupe } from "./views/Dedupe";

export default function App() {
  const { view, loadStats } = useApp();

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col bg-bg-0 text-white scanline">
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        {view === "dashboard" && <Dashboard />}
        {view === "library" && <Library />}
        {view === "recommend" && <Recommend />}
        {view === "playlist" && <PlaylistBuilder />}
        {view === "dedupe" && <Dedupe />}
      </div>
      <Player />
    </div>
  );
}

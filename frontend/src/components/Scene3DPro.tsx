import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Stars, Sphere, Torus, MeshDistortMaterial } from "@react-three/drei";
import { useRef, useMemo } from "react";
import * as THREE from "three";

/**
 * Pro view ambient 3D scene. The geometry & color shifts based on the
 * active module so each panel has its own atmosphere.
 *
 * trackid    -> green pulsing radar sphere (fingerprint matching)
 * livemix    -> twin counter-rotating tori (deck A / deck B)
 * phrasegrid -> grid of cubes pulsing in 32-bar phrases
 * hotcues    -> 8 colored cubes orbiting a central beam
 * quality    -> distorting sphere (audible defect)
 * trends     -> orbital rings (charts radar)
 * stems      -> 4 stacked layered rings (vocals/drums/bass/other)
 * gig        -> rotating cube (USB pack)
 */

type Module =
  | "trackid"
  | "livemix"
  | "phrasegrid"
  | "hotcues"
  | "quality"
  | "trends"
  | "stems"
  | "gig";

const MODULE_COLOR: Record<Module, [string, string]> = {
  trackid:    ["#00ff9d", "#00e5ff"],
  livemix:    ["#ff2ea6", "#9d00ff"],
  phrasegrid: ["#00e5ff", "#9d00ff"],
  hotcues:    ["#ff2ea6", "#fff02e"],
  quality:    ["#fff02e", "#ff2ea6"],
  trends:     ["#00e5ff", "#00ff9d"],
  stems:      ["#9d00ff", "#00e5ff"],
  gig:        ["#fff02e", "#ff2ea6"],
};

function TrackIdScene({ color }: { color: [string, string] }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    ref.current.scale.setScalar(1 + Math.sin(t * 2) * 0.08);
    ref.current.rotation.y = t * 0.2;
  });
  return (
    <Float speed={2} rotationIntensity={0.3}>
      <mesh ref={ref}>
        <icosahedronGeometry args={[1.4, 1]} />
        <meshStandardMaterial
          color={color[0]}
          emissive={color[1]}
          emissiveIntensity={0.8}
          wireframe
        />
      </mesh>
      {/* Radar pulse rings */}
      {[0, 1, 2].map((i) => (
        <Torus key={i} args={[1.6 + i * 0.6, 0.02, 16, 64]} rotation={[Math.PI / 2, 0, 0]}>
          <meshStandardMaterial
            color={color[0]}
            emissive={color[0]}
            emissiveIntensity={1.5}
            transparent
            opacity={0.5 - i * 0.15}
          />
        </Torus>
      ))}
    </Float>
  );
}

function LiveMixScene({ color }: { color: [string, string] }) {
  const a = useRef<THREE.Mesh>(null);
  const b = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (a.current) a.current.rotation.y = t * 0.5;
    if (b.current) b.current.rotation.y = -t * 0.5;
  });
  return (
    <>
      <Float speed={1.2} floatIntensity={0.4}>
        <mesh ref={a} position={[-1.6, 0, 0]}>
          <torusGeometry args={[0.9, 0.18, 16, 64]} />
          <meshStandardMaterial color={color[0]} emissive={color[0]} emissiveIntensity={1.2} metalness={0.6} />
        </mesh>
      </Float>
      <Float speed={1.2} floatIntensity={0.4}>
        <mesh ref={b} position={[1.6, 0, 0]}>
          <torusGeometry args={[0.9, 0.18, 16, 64]} />
          <meshStandardMaterial color={color[1]} emissive={color[1]} emissiveIntensity={1.2} metalness={0.6} />
        </mesh>
      </Float>
    </>
  );
}

function PhraseGridScene({ color }: { color: [string, string] }) {
  const group = useRef<THREE.Group>(null);
  const cubes = useMemo(() => {
    const out: { x: number; y: number; phase: number }[] = [];
    for (let x = -3; x <= 3; x++) {
      for (let y = -2; y <= 2; y++) {
        out.push({ x, y, phase: Math.random() * Math.PI * 2 });
      }
    }
    return out;
  }, []);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (group.current) {
      group.current.rotation.x = Math.sin(t * 0.2) * 0.2;
      group.current.rotation.y = t * 0.05;
      group.current.children.forEach((child, i) => {
        const phase = cubes[i]?.phase ?? 0;
        const beat = Math.sin(t * 2 + phase) * 0.5 + 0.5;
        child.scale.setScalar(0.3 + beat * 0.25);
        ((child as THREE.Mesh).material as THREE.MeshStandardMaterial).emissiveIntensity = 0.4 + beat * 1.5;
      });
    }
  });
  return (
    <group ref={group}>
      {cubes.map((c, i) => (
        <mesh key={i} position={[c.x * 0.9, c.y * 0.9, 0]}>
          <boxGeometry args={[0.4, 0.4, 0.4]} />
          <meshStandardMaterial color={color[0]} emissive={color[1]} emissiveIntensity={0.6} />
        </mesh>
      ))}
    </group>
  );
}

function HotCuesScene({ color }: { color: [string, string] }) {
  const group = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (group.current) group.current.rotation.y = clock.getElapsedTime() * 0.3;
  });
  const colors = ["#ff0000", "#ff8800", "#ffd700", "#ff2ea6", "#00e5ff", "#ff2ea6", "#ffd700", "#9d00ff"];
  return (
    <group ref={group}>
      {/* Central beam */}
      <mesh>
        <cylinderGeometry args={[0.06, 0.06, 4, 16]} />
        <meshStandardMaterial color={color[0]} emissive={color[0]} emissiveIntensity={2} />
      </mesh>
      {colors.map((c, i) => {
        const angle = (i / 8) * Math.PI * 2;
        return (
          <Float key={i} speed={2 + i * 0.1} floatIntensity={0.3}>
            <mesh position={[Math.cos(angle) * 2.2, Math.sin(angle) * 2.2, 0]}>
              <boxGeometry args={[0.35, 0.35, 0.35]} />
              <meshStandardMaterial color={c} emissive={c} emissiveIntensity={1.4} />
            </mesh>
          </Float>
        );
      })}
    </group>
  );
}

function QualityScene({ color }: { color: [string, string] }) {
  return (
    <Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.6}>
      <Sphere args={[1.5, 64, 64]}>
        <MeshDistortMaterial
          color={color[0]}
          emissive={color[1]}
          emissiveIntensity={0.7}
          distort={0.4}
          speed={2.5}
          metalness={0.4}
          roughness={0.2}
        />
      </Sphere>
    </Float>
  );
}

function TrendsScene({ color }: { color: [string, string] }) {
  const g1 = useRef<THREE.Mesh>(null);
  const g2 = useRef<THREE.Mesh>(null);
  const g3 = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (g1.current) g1.current.rotation.z = t * 0.4;
    if (g2.current) g2.current.rotation.z = -t * 0.3;
    if (g3.current) g3.current.rotation.z = t * 0.2;
  });
  return (
    <>
      <Torus ref={g1} args={[1.2, 0.04, 16, 100]}>
        <meshStandardMaterial color={color[0]} emissive={color[0]} emissiveIntensity={1.6} />
      </Torus>
      <Torus ref={g2} args={[1.8, 0.04, 16, 100]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial color={color[1]} emissive={color[1]} emissiveIntensity={1.4} />
      </Torus>
      <Torus ref={g3} args={[2.4, 0.04, 16, 100]} rotation={[0, Math.PI / 2, 0]}>
        <meshStandardMaterial color={color[0]} emissive={color[0]} emissiveIntensity={1.2} />
      </Torus>
    </>
  );
}

function StemsScene({ color }: { color: [string, string] }) {
  const group = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (group.current) group.current.rotation.y = clock.getElapsedTime() * 0.2;
  });
  const layerColors = ["#ff2ea6", "#fff02e", "#9d00ff", "#00e5ff"];
  return (
    <group ref={group}>
      {layerColors.map((c, i) => (
        <Torus key={i} args={[1.4, 0.08, 16, 80]} position={[0, (i - 1.5) * 0.5, 0]}>
          <meshStandardMaterial color={c} emissive={c} emissiveIntensity={1.2} />
        </Torus>
      ))}
    </group>
  );
}

function GigScene({ color }: { color: [string, string] }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    ref.current.rotation.x = t * 0.3;
    ref.current.rotation.y = t * 0.4;
  });
  return (
    <Float speed={1.5} floatIntensity={0.8}>
      <mesh ref={ref}>
        <boxGeometry args={[1.8, 1.8, 1.8]} />
        <meshStandardMaterial
          color={color[0]}
          emissive={color[1]}
          emissiveIntensity={0.9}
          metalness={0.7}
          roughness={0.3}
        />
      </mesh>
    </Float>
  );
}

const SCENES: Record<Module, React.FC<{ color: [string, string] }>> = {
  trackid: TrackIdScene,
  livemix: LiveMixScene,
  phrasegrid: PhraseGridScene,
  hotcues: HotCuesScene,
  quality: QualityScene,
  trends: TrendsScene,
  stems: StemsScene,
  gig: GigScene,
};

export function Scene3DPro({ module }: { module: Module }) {
  const Comp = SCENES[module];
  const color = MODULE_COLOR[module];
  return (
    <Canvas
      camera={{ position: [0, 0, 6], fov: 60 }}
      gl={{ antialias: true, alpha: true }}
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.25} />
      <pointLight position={[8, 8, 8]} intensity={1.2} color={color[0]} />
      <pointLight position={[-8, -8, -4]} intensity={0.9} color={color[1]} />
      <pointLight position={[0, 0, 4]} intensity={0.4} color="#9d00ff" />

      <Stars radius={70} depth={45} count={1500} factor={3} fade speed={0.4} />

      <Comp color={color} />

      <fog attach="fog" args={["#05050a", 7, 22]} />
    </Canvas>
  );
}

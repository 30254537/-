import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Stars, Text, Torus, TorusKnot } from "@react-three/drei";
import { useRef, useMemo } from "react";
import * as THREE from "three";

/**
 * Ambient 3D scene: starfield + floating torus-knot that
 * pulses with the currentTrack energy/BPM.
 */
function PulsingKnot({ energy = 5, bpm = 120 }: { energy?: number; bpm?: number }) {
  const ref = useRef<THREE.Mesh>(null);
  const matRef = useRef<THREE.MeshStandardMaterial>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    const beatFreq = bpm / 60;
    const pulse = Math.sin(t * beatFreq * Math.PI * 2) * 0.5 + 0.5;
    const scale = 1 + pulse * (0.05 + energy / 80);
    ref.current.scale.setScalar(scale);
    ref.current.rotation.x = t * 0.1;
    ref.current.rotation.y = t * 0.15;

    if (matRef.current) {
      const hue = (t * 0.02 + energy / 20) % 1;
      matRef.current.color.setHSL(hue, 0.9, 0.55);
      matRef.current.emissive.setHSL(hue, 0.9, 0.3);
      matRef.current.emissiveIntensity = 0.6 + pulse * 0.8;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.4} floatIntensity={0.6}>
      <TorusKnot ref={ref} args={[1, 0.3, 200, 32]}>
        <meshStandardMaterial
          ref={matRef}
          color="#ff2ea6"
          emissive="#9d00ff"
          emissiveIntensity={0.8}
          metalness={0.6}
          roughness={0.2}
          wireframe={false}
        />
      </TorusKnot>
    </Float>
  );
}

/** Spinning Camelot wheel in 3D — 12 segments, color-coded */
function CamelotWheel3D({ activeKey }: { activeKey?: string }) {
  const group = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (group.current) group.current.rotation.z = clock.getElapsedTime() * 0.05;
  });

  const segments = useMemo(() => {
    const segs = [];
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2;
      const x = Math.cos(angle) * 3.5;
      const y = Math.sin(angle) * 3.5;
      const keyName = `${i + 1}A`;
      const keyNameB = `${i + 1}B`;
      const isActive = activeKey === keyName || activeKey === keyNameB;
      segs.push({ angle, x, y, keyName, keyNameB, isActive });
    }
    return segs;
  }, [activeKey]);

  return (
    <group ref={group} position={[0, 0, -3]}>
      {segments.map((s, i) => (
        <group key={i} position={[s.x, s.y, 0]}>
          <Torus args={[0.3, 0.04, 16, 32]}>
            <meshStandardMaterial
              color={s.isActive ? "#00ff9d" : "#00e5ff"}
              emissive={s.isActive ? "#00ff9d" : "#00e5ff"}
              emissiveIntensity={s.isActive ? 2.5 : 0.5}
            />
          </Torus>
          <Text
            position={[0, 0, 0.1]}
            fontSize={0.25}
            color={s.isActive ? "#ffffff" : "#00e5ff"}
            anchorX="center"
            anchorY="middle"
          >
            {s.keyName.replace("A", "")}
          </Text>
        </group>
      ))}
    </group>
  );
}

export function Scene3D({
  energy = 5,
  bpm = 120,
  activeKey,
}: {
  energy?: number;
  bpm?: number;
  activeKey?: string;
}) {
  return (
    <Canvas
      camera={{ position: [0, 0, 6], fov: 60 }}
      gl={{ antialias: true, alpha: true }}
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.2} />
      <pointLight position={[10, 10, 10]} intensity={1.2} color="#ff2ea6" />
      <pointLight position={[-10, -10, -5]} intensity={0.8} color="#00e5ff" />
      <pointLight position={[0, 0, 5]} intensity={0.5} color="#9d00ff" />

      <Stars radius={80} depth={50} count={3000} factor={4} fade speed={0.5} />

      <PulsingKnot energy={energy} bpm={bpm} />
      <CamelotWheel3D activeKey={activeKey} />

      <fog attach="fog" args={["#05050a", 8, 25]} />
    </Canvas>
  );
}

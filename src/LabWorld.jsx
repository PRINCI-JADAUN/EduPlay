import { Canvas } from "@react-three/fiber";
import { ContactShadows, OrbitControls } from "@react-three/drei";

function Flask({ position, color, label }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.52, 0]} castShadow>
        <cylinderGeometry args={[0.34, 0.22, 0.72, 20, 1, true]} />
        <meshPhysicalMaterial color={color} transparent opacity={0.48} roughness={0.18} transmission={0.36} thickness={0.3} />
      </mesh>
      <mesh position={[0, 0.12, 0]}>
        <cylinderGeometry args={[0.25, 0.25, 0.12, 20]} />
        <meshPhysicalMaterial color={color} transparent opacity={0.66} roughness={0.15} />
      </mesh>
      <mesh position={[0, 0.98, 0]}>
        <cylinderGeometry args={[0.12, 0.15, 0.24, 16]} />
        <meshStandardMaterial color="#dce8e7" />
      </mesh>
      <mesh position={[0, 1.35, 0]}>
        <sphereGeometry args={[0.035, 8, 8]} />
        <meshBasicMaterial color={color} />
      </mesh>
    </group>
  );
}

function LabScene({ selectedSample, result }) {
  const solutionColor = result?.color || (selectedSample === "water" ? "#84c8bb" : "#7baed0");
  return (
    <>
      <color attach="background" args={["#c7d7d1"]} />
      <fog attach="fog" args={["#c7d7d1", 14, 36]} />
      <ambientLight intensity={1.15} />
      <directionalLight position={[5, 10, 7]} intensity={2.4} castShadow />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.06, 0]} receiveShadow>
        <planeGeometry args={[32, 32]} />
        <meshStandardMaterial color="#d8ddd5" roughness={0.92} />
      </mesh>
      <mesh position={[0, 2.5, -4.2]}>
        <boxGeometry args={[14, 5.2, 0.35]} />
        <meshStandardMaterial color="#dce6df" roughness={0.88} />
      </mesh>
      {[-3.8, 0, 3.8].map((x) => (
        <mesh key={x} position={[x, 2.6, -3.98]}>
          <boxGeometry args={[2.4, 1.35, 0.08]} />
          <meshStandardMaterial color="#99c3c4" roughness={0.4} metalness={0.06} />
        </mesh>
      ))}
      <mesh position={[0, 1.12, 0]} castShadow receiveShadow>
        <boxGeometry args={[8.5, 0.3, 3.1]} />
        <meshStandardMaterial color="#ac8b65" roughness={0.65} />
      </mesh>
      {[-3.8, -1.3, 1.3, 3.8].map((x) => (
        <mesh key={x} position={[x, 0.53, 0]} castShadow>
          <boxGeometry args={[0.2, 1, 0.2]} />
          <meshStandardMaterial color="#566762" roughness={0.7} />
        </mesh>
      ))}
      <Flask position={[-2.8, 1.28, 0]} color="#e9b880" label="A" />
      <Flask position={[-0.95, 1.28, -0.05]} color={solutionColor} label="B" />
      <Flask position={[1.05, 1.28, 0.03]} color="#a5c1dc" label="C" />
      <mesh position={[3.1, 1.55, 0]}>
        <boxGeometry args={[0.13, 0.85, 0.05]} />
        <meshStandardMaterial color={result?.color || "#e8eadf"} roughness={0.35} />
      </mesh>
      <mesh position={[3.1, 1.98, 0]}>
        <sphereGeometry args={[0.09, 12, 10]} />
        <meshStandardMaterial color="#e8ede7" roughness={0.5} />
      </mesh>
      <mesh position={[0, 3.35, -3.96]}>
        <boxGeometry args={[3.2, 0.58, 0.09]} />
        <meshStandardMaterial color="#31555a" />
      </mesh>
      <ContactShadows position={[0, 0.02, 0]} opacity={0.22} scale={14} blur={2.8} far={6} />
      <OrbitControls makeDefault target={[0, 1.2, 0]} enablePan={false} minDistance={5} maxDistance={12} minPolarAngle={0.4} maxPolarAngle={1.45} />
    </>
  );
}

export default function LabWorld({ selectedSample, result }) {
  return (
    <Canvas shadows camera={{ position: [7, 5.5, 8], fov: 44 }} dpr={[1, 1.5]}>
      <LabScene selectedSample={selectedSample} result={result} />
    </Canvas>
  );
}


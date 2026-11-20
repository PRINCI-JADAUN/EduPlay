import { Canvas, useFrame } from "@react-three/fiber";
import { ContactShadows, OrbitControls } from "@react-three/drei";
import { useEffect, useMemo, useRef } from "react";
import { createLabelTexture } from "./labelTexture.js";

function Desk({ position, color = "#947557" }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.9, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.7, 0.14, 0.88]} />
        <meshStandardMaterial color={color} roughness={0.75} />
      </mesh>
      {[-0.65, 0.65].map((x) => [-0.28, 0.28].map((z) => (
        <mesh key={`${x}-${z}`} position={[x, 0.43, z]} castShadow>
          <boxGeometry args={[0.09, 0.9, 0.09]} />
          <meshStandardMaterial color="#59665e" roughness={0.85} />
        </mesh>
      )))}
      <mesh position={[0, 0.58, 0.83]} castShadow>
        <boxGeometry args={[1.7, 0.85, 0.1]} />
        <meshStandardMaterial color="#596c63" roughness={0.8} />
      </mesh>
    </group>
  );
}

function Bookcase({ x, library = false }) {
  return (
    <group position={[x, 0, -3.2]}>
      <mesh position={[0, 1.55, 0]} castShadow>
        <boxGeometry args={[2, 3.1, 0.65]} />
        <meshStandardMaterial color={library ? "#75523b" : "#54716a"} roughness={0.8} />
      </mesh>
      {[0.7, 1.5, 2.3].map((y) => (
        <mesh key={y} position={[0, y, 0.08]}>
          <boxGeometry args={[1.92, 0.09, 0.68]} />
          <meshStandardMaterial color="#d0b38b" roughness={0.8} />
        </mesh>
      ))}
      {Array.from({ length: 10 }, (_, index) => (
        <mesh key={index} position={[-0.84 + (index % 5) * 0.41, 0.99 + Math.floor(index / 5) * 0.8, 0.08]}>
          <boxGeometry args={[0.28, 0.48, 0.34]} />
          <meshStandardMaterial color={["#9a6951", "#879a78", "#b39a69", "#72899a", "#a57a63"][index % 5]} roughness={0.95} />
        </mesh>
      ))}
    </group>
  );
}

function Chair({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.53, 0]} castShadow>
        <boxGeometry args={[0.62, 0.09, 0.58]} />
        <meshStandardMaterial color="#b87953" roughness={0.78} />
      </mesh>
      <mesh position={[0, 0.88, 0.27]} castShadow>
        <boxGeometry args={[0.62, 0.65, 0.08]} />
        <meshStandardMaterial color="#b87953" roughness={0.78} />
      </mesh>
      {[-0.22, 0.22].map((x) => [-0.2, 0.2].map((z) => (
        <mesh key={`${x}-${z}`} position={[x, 0.27, z]} castShadow>
          <boxGeometry args={[0.055, 0.52, 0.055]} />
          <meshStandardMaterial color="#505d59" metalness={0.22} roughness={0.6} />
        </mesh>
      )))}
    </group>
  );
}

function Student({ position, shirt = "#648da1", hair = "#493c34" }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.89, 0]} castShadow>
        <capsuleGeometry args={[0.2, 0.38, 5, 10]} />
        <meshStandardMaterial color={shirt} roughness={0.82} />
      </mesh>
      <mesh position={[0, 1.29, -0.02]} castShadow>
        <sphereGeometry args={[0.21, 14, 12]} />
        <meshStandardMaterial color="#c99170" roughness={0.86} />
      </mesh>
      <mesh position={[0, 1.39, -0.075]} castShadow>
        <sphereGeometry args={[0.22, 14, 10, 0, Math.PI * 2, 0, Math.PI * 0.52]} />
        <meshStandardMaterial color={hair} roughness={0.9} />
      </mesh>
      {[-1, 1].map((side) => (
        <mesh key={side} position={[side * 0.25, 0.91, -0.2]} rotation={[0.5, 0, side * -0.3]} castShadow>
          <capsuleGeometry args={[0.055, 0.32, 4, 8]} />
          <meshStandardMaterial color={shirt} roughness={0.82} />
        </mesh>
      ))}
    </group>
  );
}

function Teacher({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.92, 0]} castShadow>
        <capsuleGeometry args={[0.23, 0.58, 5, 10]} />
        <meshStandardMaterial color="#557c72" roughness={0.78} />
      </mesh>
      <mesh position={[0, 1.59, 0]} castShadow>
        <sphereGeometry args={[0.22, 16, 14]} />
        <meshStandardMaterial color="#c98e6d" roughness={0.86} />
      </mesh>
      <mesh position={[0, 1.69, -0.065]} castShadow>
        <sphereGeometry args={[0.225, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.53]} />
        <meshStandardMaterial color="#382d29" roughness={0.9} />
      </mesh>
      {[-1, 1].map((side) => (
        <mesh key={side} position={[side * 0.3, 1.02, -0.03]} rotation={[0, 0, side * 0.34]} castShadow>
          <capsuleGeometry args={[0.065, 0.48, 4, 8]} />
          <meshStandardMaterial color="#557c72" roughness={0.78} />
        </mesh>
      ))}
      <mesh position={[0.48, 1.25, -0.15]} rotation={[0.1, 0, -0.2]}>
        <cylinderGeometry args={[0.012, 0.012, 0.72, 8]} />
        <meshStandardMaterial color="#dfc889" />
      </mesh>
    </group>
  );
}

function ClassroomSetup() {
  const desks = [
    [-4.3, 1.7], [-1.45, 1.7], [1.45, 1.7], [4.3, 1.7],
    [-2.9, 4.1], [0, 4.1], [2.9, 4.1],
  ];
  const uniforms = ["#648da1", "#8d7188", "#bd825f", "#718c70", "#7584aa", "#af9866", "#698f8c"];
  return (
    <>
      {desks.map(([x, z], index) => (
        <group key={`${x}-${z}`}>
          <Desk position={[x, 0, z]} />
          <Chair position={[x, 0, z + 0.7]} />
          <Student position={[x, 0, z + 0.73]} shirt={uniforms[index]} hair={index % 2 ? "#332c29" : "#6b4935"} />
        </group>
      ))}
      <Teacher position={[0, 0, -2.75]} />
    </>
  );
}

function LabBench({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.03, 0]} castShadow receiveShadow>
        <boxGeometry args={[3.1, 0.14, 1.25]} />
        <meshStandardMaterial color="#424f4e" roughness={0.42} metalness={0.14} />
      </mesh>
      {[-1.1, 1.1].map((x) => (
        <group key={x} position={[x, 0, 0]}>
          <mesh position={[0, 0.49, 0]} castShadow>
            <boxGeometry args={[0.58, 0.92, 0.95]} />
            <meshStandardMaterial color="#b8c2bb" roughness={0.72} />
          </mesh>
          <mesh position={[0, 0.49, 0.49]}>
            <boxGeometry args={[0.48, 0.78, 0.035]} />
            <meshStandardMaterial color="#87958e" roughness={0.74} />
          </mesh>
        </group>
      ))}
      {[-1.35, 1.35].map((x) => (
        <mesh key={x} position={[x, 0.52, 0]} castShadow>
          <cylinderGeometry args={[0.045, 0.05, 0.95, 10]} />
          <meshStandardMaterial color="#9ba8a1" metalness={0.45} roughness={0.42} />
        </mesh>
      ))}
    </group>
  );
}

function LabBottle({ position, color = "#82bba8" }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.26, 0]} castShadow>
        <cylinderGeometry args={[0.13, 0.16, 0.42, 16]} />
        <meshPhysicalMaterial color="#dce8df" transparent opacity={0.5} roughness={0.16} />
      </mesh>
      <mesh position={[0, 0.18, 0]}>
        <cylinderGeometry args={[0.12, 0.14, 0.16, 16]} />
        <meshStandardMaterial color={color} transparent opacity={0.85} />
      </mesh>
      <mesh position={[0, 0.52, 0]}>
        <cylinderGeometry args={[0.06, 0.08, 0.12, 12]} />
        <meshStandardMaterial color="#e1e6df" roughness={0.32} />
      </mesh>
    </group>
  );
}

function Microscope({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.08, 0]} castShadow>
        <boxGeometry args={[0.38, 0.06, 0.3]} />
        <meshStandardMaterial color="#586966" metalness={0.35} roughness={0.42} />
      </mesh>
      <mesh position={[0, 0.34, -0.04]} rotation={[0, 0, -0.28]} castShadow>
        <capsuleGeometry args={[0.055, 0.42, 4, 8]} />
        <meshStandardMaterial color="#75827d" metalness={0.42} roughness={0.36} />
      </mesh>
      <mesh position={[0, 0.55, -0.1]} rotation={[0, 0, -0.28]}>
        <cylinderGeometry args={[0.055, 0.06, 0.16, 12]} />
        <meshStandardMaterial color="#243b3d" roughness={0.3} />
      </mesh>
      <mesh position={[0.13, 0.25, -0.03]}>
        <cylinderGeometry args={[0.075, 0.075, 0.05, 12]} />
        <meshStandardMaterial color="#9cbab1" />
      </mesh>
    </group>
  );
}

function ComputerStation({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.28, -0.12]} castShadow>
        <boxGeometry args={[0.62, 0.38, 0.07]} />
        <meshStandardMaterial color="#475b58" roughness={0.4} />
      </mesh>
      <mesh position={[0, 0.29, -0.078]}>
        <planeGeometry args={[0.53, 0.29]} />
        <meshBasicMaterial color="#75b9bc" />
      </mesh>
      <mesh position={[0, 0.08, -0.06]}>
        <boxGeometry args={[0.12, 0.04, 0.12]} />
        <meshStandardMaterial color="#65736d" metalness={0.25} />
      </mesh>
      <mesh position={[0, 0.035, 0.16]} castShadow>
        <boxGeometry args={[0.52, 0.045, 0.2]} />
        <meshStandardMaterial color="#aebbb2" roughness={0.48} />
      </mesh>
    </group>
  );
}

function LabSetup({ name }) {
  const subject = name.toLowerCase();
  const physics = subject.includes("phys");
  const biology = subject.includes("bio");
  const computers = subject.includes("computer") || subject.includes("informatics");
  const equipmentPositions = [-4.55, -3.8, -3.05, 3.05, 3.8, 4.55];

  return (
    <>
      <LabBench position={[-3.8, 0, 0.25]} />
      <LabBench position={[3.8, 0, 0.25]} />
      <LabBench position={[0, 0, 2.5]} />
      {computers ? (
        <>
          {[-4.25, -3.35, 3.35, 4.25].map((x) => <ComputerStation key={x} position={[x, 1.11, 0.22]} />)}
          {[-0.65, 0.65].map((x) => <ComputerStation key={x} position={[x, 1.11, 2.48]} />)}
        </>
      ) : subject.includes("chem") ? (
        <>
          {equipmentPositions.map((x, index) => <LabBottle key={x} position={[x, 1.1, 0.2]} color={["#71b59a", "#d9a367", "#819ed0"][index % 3]} />)}
          {[-0.75, 0.75].map((x) => (
            <group key={x} position={[x, 1.1, 2.45]}>
              <mesh position={[0, 0.19, 0]} castShadow>
                <cylinderGeometry args={[0.12, 0.2, 0.38, 18]} />
                <meshPhysicalMaterial color="#c7ded5" transparent opacity={0.55} roughness={0.18} />
              </mesh>
              <mesh position={[0, 0.12, 0]}>
                <cylinderGeometry args={[0.15, 0.18, 0.12, 18]} />
                <meshStandardMaterial color={x < 0 ? "#e1a36f" : "#79b8a0"} transparent opacity={0.84} />
              </mesh>
            </group>
          ))}
        </>
      ) : biology ? (
        <>
          {[-4.5, -3.75, -3, 3, 3.75, 4.5].map((x) => <Microscope key={x} position={[x, 1.12, 0.15]} />)}
          {[-0.75, 0.75].map((x) => (
            <group key={x} position={[x, 1.1, 2.45]}>
              <mesh position={[0, 0.12, 0]} castShadow>
                <cylinderGeometry args={[0.15, 0.12, 0.22, 14]} />
                <meshStandardMaterial color="#ad8064" roughness={0.84} />
              </mesh>
              <mesh position={[0, 0.44, 0]} castShadow>
                <sphereGeometry args={[0.24, 12, 10]} />
                <meshStandardMaterial color="#5e9a6e" roughness={0.88} />
              </mesh>
              <mesh position={[0.15, 0.51, 0]} rotation={[0, 0, -0.6]}>
                <sphereGeometry args={[0.13, 10, 8]} />
                <meshStandardMaterial color="#78ac72" roughness={0.88} />
              </mesh>
            </group>
          ))}
        </>
      ) : physics ? (
        <>
          {equipmentPositions.map((x, index) => (
            <group key={x} position={[x, 1.12, 0.22]}>
              <mesh position={[0, 0.1, 0]} castShadow>
                <boxGeometry args={[0.48, 0.18, 0.34]} />
                <meshStandardMaterial color={index % 2 ? "#687c7a" : "#ad9866"} metalness={0.22} roughness={0.5} />
              </mesh>
              <mesh position={[0, 0.2, -0.04]}>
                <boxGeometry args={[0.28, 0.07, 0.04]} />
                <meshBasicMaterial color="#b9ddc0" />
              </mesh>
              <mesh position={[-0.12, 0.25, 0.07]} rotation={[Math.PI / 2, 0, 0]}>
                <torusGeometry args={[0.07, 0.008, 6, 18]} />
                <meshStandardMaterial color="#d7bd7a" metalness={0.35} />
              </mesh>
            </group>
          ))}
        </>
      ) : (
        <>
          {equipmentPositions.map((x, index) => <LabBottle key={x} position={[x, 1.1, 0.2]} color={["#71b59a", "#d9a367", "#819ed0"][index % 3]} />)}
          <Microscope position={[-0.65, 1.12, 2.44]} />
          <LabBottle position={[0.65, 1.1, 2.44]} color="#87a9d1" />
        </>
      )}
      {[-5.2, -3.8, 3.8, 5.2].map((x) => (
        <group key={x} position={[x, 0, 1.65]}>
          <mesh position={[0, 0.6, 0]} castShadow>
            <cylinderGeometry args={[0.27, 0.31, 0.1, 16]} />
            <meshStandardMaterial color="#527c7c" roughness={0.5} />
          </mesh>
          <mesh position={[0, 0.3, 0]}>
            <cylinderGeometry args={[0.035, 0.045, 0.55, 10]} />
            <meshStandardMaterial color="#6e817b" metalness={0.35} />
          </mesh>
      </group>
      ))}
    </>
  );
}

function ActivityCard({ item, position, highlighted = false, content }) {
  const label = item.replaceAll("-", " ").toUpperCase();
  const texture = useMemo(() => createLabelTexture(label, content || "LEARNING OBJECT", "#f0eadc"), [content, label]);
  useEffect(() => () => texture.dispose(), [texture]);

  return (
    <group position={position}>
      {[2, 1, 0].map((layer) => (
        <mesh key={layer} position={[layer * -0.035, layer * 0.012, layer * -0.025]} rotation={[0, layer * -0.035, 0]} castShadow receiveShadow>
          <boxGeometry args={[0.52, 0.025, 0.38]} />
          <meshStandardMaterial color={highlighted && layer === 0 ? "#e4d59f" : "#f4f0e5"} roughness={0.78} />
        </mesh>
      ))}
      <mesh position={[0, 0.014, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[0.48, 0.12]} />
        <meshBasicMaterial map={texture} toneMapped={false} />
      </mesh>
      {highlighted && (
        <mesh position={[0, 0.06, 0]}>
          <boxGeometry args={[0.56, 0.015, 0.42]} />
          <meshBasicMaterial color="#a9d8b5" wireframe transparent opacity={0.8} />
        </mesh>
      )}
    </group>
  );
}

function ActivityBeaker({ position, filled = false, highlighted = false }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.16, 0]} castShadow>
        <cylinderGeometry args={[0.13, 0.1, 0.34, 20, 1, true]} />
        <meshPhysicalMaterial color="#dce8df" transparent opacity={0.42} roughness={0.16} />
      </mesh>
      <mesh position={[0, filled ? 0.075 : 0.025, 0]}>
        <cylinderGeometry args={[0.095, 0.095, filled ? 0.12 : 0.025, 20]} />
        <meshStandardMaterial color={highlighted ? "#9dcfac" : "#e1a36f"} transparent opacity={0.82} />
      </mesh>
      <mesh position={[0, 0.35, 0]}>
        <cylinderGeometry args={[0.085, 0.105, 0.08, 20, 1, true]} />
        <meshPhysicalMaterial color="#dce8df" transparent opacity={0.48} roughness={0.16} />
      </mesh>
    </group>
  );
}

function ActivityRuler({ position }) {
  return (
    <group position={position}>
      <mesh castShadow>
        <boxGeometry args={[0.62, 0.035, 0.13]} />
        <meshStandardMaterial color="#e2c47e" roughness={0.55} />
      </mesh>
      {Array.from({ length: 9 }, (_, index) => (
        <mesh key={index} position={[-0.27 + index * 0.067, 0.02, -0.035]}>
          <boxGeometry args={[0.008, 0.008, index % 2 === 0 ? 0.045 : 0.025]} />
          <meshBasicMaterial color="#4d5546" />
        </mesh>
      ))}
    </group>
  );
}

function ActivityObject({ item, position, highlighted = false, filled = false, content }) {
  if (item.includes("beaker") || item.includes("sample")) {
    return <ActivityBeaker position={position} filled={filled || item.includes("sample")} highlighted={highlighted} />;
  }
  if (item.includes("computer")) return <ComputerStation position={position} />;
  if (item.includes("ruler")) return <ActivityRuler position={position} />;
  return <ActivityCard item={item} position={position} highlighted={highlighted} content={content} />;
}

function AnimatedActivityObject({ item, position, initialPosition = position, motion = "stationary", ...props }) {
  const groupRef = useRef(null);
  const originRef = useRef(initialPosition);
  const progressRef = useRef(motion === "stationary" ? 1 : 0);

  useEffect(() => {
    if (!groupRef.current) return;
    originRef.current = groupRef.current.position.toArray();
    progressRef.current = 0;
  }, [motion]);

  useFrame((state, delta) => {
    if (!groupRef.current || motion === "stationary") return;
    progressRef.current = Math.min(1, progressRef.current + delta / (motion === "carried" ? 0.65 : 0.4));
    const progress = progressRef.current;
    const eased = progress * progress * (3 - 2 * progress);
    const lift = motion === "carried"
      ? Math.sin(Math.PI * eased) * 0.48 + (progress === 1 ? Math.sin(state.clock.elapsedTime * 4) * 0.025 : 0)
      : 0;
    const origin = originRef.current;
    groupRef.current.position.set(
      origin[0] + (position[0] - origin[0]) * eased,
      origin[1] + (position[1] - origin[1]) * eased + lift,
      origin[2] + (position[2] - origin[2]) * eased,
    );
    groupRef.current.rotation.z = motion === "carried"
      ? Math.sin(state.clock.elapsedTime * 3) * 0.045
      : groupRef.current.rotation.z * Math.max(0, 1 - delta * 8);
  });

  return (
    <group ref={groupRef} position={initialPosition}>
      <ActivityObject item={item} position={[0, 0, 0]} {...props} />
    </group>
  );
}

function ActivityStage({ activity, currentStep, carriedItem, placedItems, stepIndex, surfaceY }) {
  if (!activity) return null;

  const inventory = activity.simulation?.items || [];
  const sourceItems = currentStep?.action === "pick"
    ? inventory.filter((item) => !placedItems.includes(item))
    : [];
  const workbenchItems = [...new Set([
    ...placedItems,
    carriedItem,
    currentStep?.action !== "pick" ? currentStep?.item : "",
  ].filter(Boolean))];
  const activeItems = workbenchItems.length ? workbenchItems : currentStep?.item ? [currentStep.item] : [];

  return (
    <group position={[2.2, 0, 0.2]}>
      <mesh position={[0, surfaceY + 0.012, -0.24]} receiveShadow>
        <boxGeometry args={[1.48, 0.035, 0.36]} />
        <meshStandardMaterial color="#415a50" roughness={0.72} />
      </mesh>
      <mesh position={[0, surfaceY + 0.034, -0.24]}>
        <boxGeometry args={[1.38, 0.012, 0.27]} />
        <meshStandardMaterial color="#d9c99f" roughness={0.85} />
      </mesh>
      {currentStep?.action === "sort" && (
        <group position={[0, surfaceY + 0.035, 0.23]}>
          <mesh>
            <boxGeometry args={[1.42, 0.025, 0.62]} />
            <meshStandardMaterial color="#405a55" roughness={0.88} />
          </mesh>
          {[-0.46, 0, 0.46].map((x, index) => (
            <mesh key={x} position={[x, 0.016, 0]}>
              <boxGeometry args={[0.42, 0.012, 0.48]} />
              <meshStandardMaterial color={["#759d8c", "#c5a96f", "#7293a0"][index]} transparent opacity={0.9} />
            </mesh>
          ))}
        </group>
      )}
      {sourceItems.map((item, index) => (
        <AnimatedActivityObject
          key={`source-${item}`}
          item={item}
          position={[(index - (sourceItems.length - 1) / 2) * 0.31, surfaceY + 0.04, -0.24]}
          highlighted={item === currentStep?.item}
          content={activity.title}
        />
      ))}
      {activeItems.map((item, index) => (
        <AnimatedActivityObject
          key={`bench-${item}`}
          item={item}
          position={[(index - (activeItems.length - 1) / 2) * 0.28, surfaceY + (currentStep?.action === "place" && item === carriedItem ? 0.16 : currentStep?.action === "sort" ? 0.11 : 0.04), 0.23]}
          initialPosition={item === carriedItem && currentStep?.action === "place"
            ? [(sourceItems.indexOf(item) - (sourceItems.length - 1) / 2) * 0.31, surfaceY + 0.04, -0.24]
            : undefined}
          motion={item === carriedItem && currentStep?.action === "place"
            ? "carried"
            : placedItems[placedItems.length - 1] === item
              ? "placed"
              : "stationary"}
          highlighted={item === currentStep?.item}
          filled={stepIndex > 3}
          content={activity.title}
        />
      ))}
    </group>
  );
}

function RoomScene({ name, roomType, activity, currentStep, carriedItem, placedItems, stepIndex }) {
  const isLibrary = roomType === "library";
  const isLab = roomType === "laboratory";
  const furnitureColor = isLab ? "#9a7958" : "#947557";
  const roomSign = useMemo(
    () => createLabelTexture(isLibrary ? "SCHOOL LIBRARY" : name.toUpperCase(), `CLASSROOM · ${roomType.toUpperCase()}`),
    [isLibrary, name, roomType],
  );
  const boardTexture = useMemo(
    () => createLabelTexture(
      isLibrary ? "SCHOOL LIBRARY" : name.toUpperCase(),
      isLab ? "SAFETY · METHOD · OBSERVATION" : "TODAY'S LESSON · PRACTICE · REVIEW",
      "#e4e6d8",
    ),
    [isLab, isLibrary, name],
  );
  useEffect(() => () => roomSign.dispose(), [roomSign]);
  useEffect(() => () => boardTexture.dispose(), [boardTexture]);
  return (
    <>
      <color attach="background" args={[isLab ? "#bfcec7" : "#c8d6ca"]} />
      <fog attach="fog" args={[isLab ? "#bfcec7" : "#c8d6ca", 14, 32]} />
      <ambientLight intensity={1.15} />
      <directionalLight position={[5, 9, 6]} intensity={2} castShadow />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.07, 0]} receiveShadow>
        <planeGeometry args={[22, 18]} />
        <meshStandardMaterial color="#d6d5ca" roughness={0.92} />
      </mesh>
      <mesh position={[0, 2.5, -4.5]}>
        <boxGeometry args={[14, 5, 0.3]} />
        <meshStandardMaterial color="#e1e7dc" roughness={0.88} />
      </mesh>
      {[-4, -1.3, 1.3, 4].map((x) => (
        <mesh key={x} position={[x, 2.65, -4.3]}>
          <boxGeometry args={[2.15, 1.35, 0.06]} />
          <meshStandardMaterial color="#93bdc0" roughness={0.35} />
        </mesh>
      ))}
      <mesh position={[0, 2.1, -4.28]}>
        <boxGeometry args={[5.4, 1.55, 0.09]} />
        <meshStandardMaterial color={isLibrary ? "#536e69" : "#52695f"} roughness={0.85} />
      </mesh>
      <mesh position={[0, 3.04, -4.18]}>
        <boxGeometry args={[5.4, 0.08, 0.12]} />
        <meshStandardMaterial color="#d4ba84" />
      </mesh>
      <mesh position={[0, 2.27, -4.16]}>
        <planeGeometry args={[4.8, 1.15]} />
        <meshBasicMaterial map={boardTexture} toneMapped={false} />
      </mesh>
      <mesh position={[0, 3.6, -4.23]}>
        <boxGeometry args={[3.8, 0.32, 0.1]} />
        <meshStandardMaterial color="#38564e" />
      </mesh>
      {isLibrary ? (
        <>
          <Desk position={[-2.2, 0, 0.2]} color={furnitureColor} />
          <Desk position={[2.2, 0, 0.2]} color={furnitureColor} />
        </>
      ) : isLab ? (
        <LabSetup name={name} />
      ) : (
        <ClassroomSetup />
      )}
      {activity && (
        isLab
          ? <LabBench position={[2.2, 0, 0.2]} />
          : <Desk position={[2.2, 0, 0.2]} color={furnitureColor} />
      )}
      {isLibrary && [-4.3, 4.3].map((x) => <Bookcase key={x} x={x} library />)}
      <ActivityStage
        activity={activity}
        currentStep={currentStep}
        carriedItem={carriedItem}
        placedItems={placedItems}
        stepIndex={stepIndex}
        surfaceY={isLab ? 1.1 : 0.97}
      />
      <ContactShadows position={[0, 0, 0]} opacity={0.22} scale={16} blur={3} far={6} />
      <OrbitControls makeDefault target={activity ? [2.2, 1.1, 0.2] : [0, 1.1, 0]} enablePan={false} minDistance={4} maxDistance={11} minPolarAngle={0.4} maxPolarAngle={1.45} />
      <mesh position={[0, 3.65, -4.1]}>
        <planeGeometry args={[5.5, 0.42]} />
        <meshStandardMaterial map={roomSign} />
      </mesh>
    </>
  );
}

export default function LearningRoomWorld({
  name,
  roomType,
  activity = null,
  currentStep = null,
  carriedItem = "",
  placedItems = [],
  stepIndex = 0,
}) {
  return (
    <Canvas shadows camera={{ position: [7, 5.2, 8], fov: 44 }} dpr={[1, 1.5]}>
      <RoomScene
        name={name}
        roomType={roomType}
        activity={activity}
        currentStep={currentStep}
        carriedItem={carriedItem}
        placedItems={placedItems}
        stepIndex={stepIndex}
      />
    </Canvas>
  );
}

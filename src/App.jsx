import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Atom,
  BadgeCheck,
  BookOpen,
  BrainCircuit,
  CircleHelp,
  Coins,
  ExternalLink,
  FlaskConical,
  GraduationCap,
  Hand,
  Leaf,
  LockKeyhole,
  LogOut,
  Pause,
  Play,
  ShieldCheck,
  Sparkles,
  Star,
  Scale,
  Trophy,
  X,
} from "lucide-react";
import { api, getGuestId, supabase, withGuestId } from "./api.js";

const GameWorld = lazy(() => import("./GameWorld.jsx"));
const LabWorld = lazy(() => import("./LabWorld.jsx"));
const LearningRoomWorld = lazy(() => import("./LearningRoomWorld.jsx"));

const INITIAL_CLASSES = Array.from({ length: 12 }, (_, index) => index + 1);
function Badge({ children, tone = "mint" }) {
  return <span className={`eyebrow-badge eyebrow-${tone}`}>{children}</span>;
}

function PlayerCard({ player, onProgress }) {
  return (
    <div className="hud-player panel-glass">
      <div className="avatar-token">{player.display_name.slice(0, 1).toUpperCase()}</div>
      <div className="player-copy">
        <strong>{player.display_name}</strong>
        <span>CLASS {player.class}</span>
      </div>
      <div className="hud-divider" />
      <div className="hud-stat"><Star size={16} /><span>{player.xp} XP</span></div>
      <div className="hud-stat hud-coins"><Coins size={16} /><span>{player.coins}</span></div>
      <button className="icon-button hud-help" aria-label="View progress" onClick={onProgress}><Trophy size={17} /></button>
    </div>
  );
}

function Welcome({ classes, selectedClass, setSelectedClass, name, setName, onStart, loading, error, authBusy, onAuth, onGuest, authMessage }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState("signin");

  const submitAuth = (event) => {
    event.preventDefault();
    onAuth(authMode, email, password);
  };

  return (
    <div className="welcome-screen">
      <div className="welcome-backdrop">
        <div className="welcome-orb orb-one" />
        <div className="welcome-orb orb-two" />
        <div className="campus-silhouette"><span /><span /><span /><span /><span /></div>
      </div>
      <header className="welcome-header">
        <div className="brand-lockup"><div className="brand-mark"><Atom size={21} /></div><span>EDU<span>PLAY</span></span></div>
        <Badge>LEARNING WORLD · BETA</Badge>
        <div className="safe-label"><ShieldCheck size={15} /> Safe virtual experiments</div>
      </header>
      <main className="welcome-content">
        <section className="welcome-story">
          <div className="story-kicker"><span className="pulse-dot" /> YOUR NEXT SCHOOL DAY IS AN ADVENTURE</div>
          <h1>Don't just learn it.<br /><span>Step inside.</span></h1>
          <p>Explore a living school campus, run your first virtual chemistry experiment, and learn by doing.</p>
          <div className="welcome-features">
            <div><span className="feature-icon feature-mint"><Leaf size={17} /></span><span><b>Explore</b><small>A 3D school campus</small></span></div>
            <div><span className="feature-icon feature-amber"><FlaskConical size={17} /></span><span><b>Experiment</b><small>A safe virtual lab</small></span></div>
            <div><span className="feature-icon feature-blue"><Trophy size={17} /></span><span><b>Earn rewards</b><small>XP, coins and progress</small></span></div>
          </div>
          <div className="welcome-note"><span className="note-line" />First stop: Class 10 Chemistry · pH Explorer</div>
        </section>

        <section className="launch-card panel-glass">
          <div className="launch-card-top">
            <Badge tone="sand">START YOUR JOURNEY</Badge>
            <span className="launch-step">01 <i>/ 02</i></span>
          </div>
          <h2>Meet your student</h2>
          <p className="launch-subtitle">Set up a profile to enter the campus.</p>
          <label className="field-label" htmlFor="student-name">STUDENT NAME</label>
          <input id="student-name" className="form-control edu-input" value={name} onChange={(event) => setName(event.target.value)} maxLength={40} placeholder="What should we call you?" />
          <label className="field-label mt-3" htmlFor="student-class">YOUR CLASS</label>
          <div className="class-select-wrap">
            <GraduationCap size={17} />
            <select id="student-class" className="form-select edu-select" value={selectedClass} onChange={(event) => setSelectedClass(Number(event.target.value))}>
              {classes.map((classNumber) => <option key={classNumber} value={classNumber}>Class {classNumber}</option>)}
            </select>
            <ArrowRight size={16} />
          </div>
          {error && <div className="notice notice-error"><CircleHelp size={16} />{error}</div>}
          <button className="primary-button launch-button" disabled={loading || !name.trim()} onClick={onStart}>
            {loading ? <span className="spinner-border spinner-border-sm" /> : <><Play size={16} fill="currentColor" /> Enter the campus</>}
          </button>
          <div className="guest-caption"><ShieldCheck size={13} /> No password needed for local guest play.</div>
          {supabase && (
            <div className="auth-section">
              <div className="auth-divider"><span />OR USE YOUR ACCOUNT<span /></div>
              <form onSubmit={submitAuth}>
                <input className="form-control edu-input auth-input" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email address" required />
                <input className="form-control edu-input auth-input" type="password" autoComplete={authMode === "signin" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" minLength={8} required />
                <button className="secondary-button auth-submit" type="submit" disabled={authBusy}>
                  {authBusy ? "Connecting…" : authMode === "signin" ? "Log in with Supabase" : "Create account"}
                </button>
              </form>
              <button className="text-button auth-switch" onClick={() => setAuthMode(authMode === "signin" ? "signup" : "signin")}>
                {authMode === "signin" ? "New here? Create an account" : "Already have an account? Log in"}
              </button>
              {authMessage && <div className="auth-message">{authMessage}</div>}
            </div>
          )}
        </section>
      </main>
      <footer className="welcome-footer"><span>EDUPLAY · LEARN BY EXPLORING</span><span>Built for curious minds, Classes 1–12</span></footer>
    </div>
  );
}

function LearningRoom({ player, room, practicals, busy, error, onStartPractical, onStartActivity, onBack, onOpenSubject }) {
  const activities = room.chapters?.flatMap((chapter) => chapter.activities.map((activity) => ({
    ...activity,
    chapter: chapter.title,
    syllabusUrl: chapter.syllabus_url,
  }))) || [];
  const syllabusUrl = room.chapters?.find((chapter) => chapter.syllabus_url)?.syllabus_url;
  const isLibrary = room.room_type === "library";

  return (
    <div className="learning-room-screen">
      <div className="learning-room-world"><Suspense fallback={<div className="world-loading">Opening the classroom…</div>}><LearningRoomWorld name={room.name} roomType={room.room_type} /></Suspense></div>
      <header className="lab-topbar">
        <button className="room-back" onClick={onBack}><ArrowLeft size={16} /><span>CAMPUS</span></button>
        <div className="lab-brand"><div className="brand-mark"><BookOpen size={17} /></div><span>EDU<span>PLAY</span></span><i>/</i><span>{room.name.toUpperCase()}</span></div>
        <div className="lab-location"><span className="live-dot" /> CLASS {player.class}</div>
        <div className="room-level">LEVEL {player.level} <Star size={14} /> {player.xp} XP</div>
      </header>
      <aside className="room-sidebar panel-glass">
        <div className="room-kicker"><Badge tone={isLibrary ? "sand" : "mint"}>{isLibrary ? "CAMPUS LIBRARY" : room.room_type === "laboratory" ? "VIRTUAL LABORATORY" : "CLASSROOM"}</Badge><span>CLASS {player.class}</span></div>
        <h1>{isLibrary ? `Welcome to the library, ${player.display_name}.` : room.name}</h1>
        <p className="room-intro">{isLibrary ? "Browse this class's subjects, syllabus references, and learning resources." : "Choose a hands-on learning activity or explore the syllabus reference for this subject."}</p>

        {isLibrary ? (
          <>
            <div className="room-section-heading">CLASS {player.class} SUBJECTS <span>{room.subjects.length} ROOMS</span></div>
            <div className="library-subject-list">
              {room.subjects.map((subject) => (
                <article className="library-subject-card" key={subject.slug}>
                  <div><strong>{subject.name}</strong><small>{subject.activity_count} activity · {subject.building}</small></div>
                  {subject.syllabus_url && <a href={subject.syllabus_url} target="_blank" rel="noreferrer" aria-label={`${subject.name} syllabus`}><ExternalLink size={14} /></a>}
                  <button className="text-button" onClick={() => onOpenSubject(subject.slug)} aria-label={`Enter ${subject.name} room`}>ENTER</button>
                </article>
              ))}
            </div>
            <div className="room-resource-list">
              {room.resources.map((resource) => <a key={resource.provider} href={resource.url} target="_blank" rel="noreferrer"><ExternalLink size={13} /><span>{resource.title}</span></a>)}
            </div>
          </>
        ) : (
          <>
            {syllabusUrl && <a className="syllabus-link" href={syllabusUrl} target="_blank" rel="noreferrer"><BookOpen size={14} /> View the CBSE syllabus reference <ExternalLink size={12} /></a>}
            <div className="room-section-heading">LEARNING ACTIVITIES <span>{activities.length + practicals.length}</span></div>
            <div className="room-activity-list">
              {practicals.map((practical, index) => (
                <article className="room-activity-card" key={practical.slug}>
                  <div className="activity-card-top"><span className="activity-index">P{String(index + 1).padStart(2, "0")}</span><Badge tone="sand">PRACTICAL</Badge></div>
                  <strong>{practical.title}</strong>
                  <small>{practical.chapter} · {practical.estimated_minutes} min</small>
                  <button className="primary-button room-start-button" disabled={busy} onClick={() => onStartPractical(practical)}>Enter virtual experiment <ArrowRight size={14} /></button>
                </article>
              ))}
              {activities.map((activity, index) => (
                <article className="room-activity-card" key={activity.slug}>
                  <div className="activity-card-top"><span className="activity-index">A{String(index + 1).padStart(2, "0")}</span><Badge>{activity.activity_type}</Badge></div>
                  <strong>{activity.title}</strong>
                  <small>{activity.chapter} · {activity.steps_count} guided steps</small>
                  <p>{activity.objective}</p>
                  <button className="secondary-button room-start-button" disabled={busy} onClick={() => onStartActivity(activity)}>Start activity <ArrowRight size={14} /></button>
                  <div className="room-resource-links">
                    {activity.resources.map((resource) => <a key={resource.provider} href={resource.url} target="_blank" rel="noreferrer"><ExternalLink size={12} />{resource.provider}</a>)}
                  </div>
                </article>
              ))}
              {!activities.length && !practicals.length && <div className="room-empty">Activities are being prepared for this room. Use the syllabus link or visit the library while more are added.</div>}
            </div>
          </>
        )}
        {error && <div className="notice notice-error room-error">{error}</div>}
        {!isLibrary && room.name.toLowerCase().includes("laboratory") && <div className="lab-safety"><ShieldCheck size={14} /><span>Every experiment is a virtual simulation. Never handle real chemicals or equipment for a game activity.</span></div>}
      </aside>
      <div className="room-scene-caption panel-glass"><span className="scene-dot" /> {isLibrary ? "SCHOOL LIBRARY" : `${room.name.toUpperCase()} · CLASS ${player.class}`} <i>·</i> DRAG TO LOOK AROUND</div>
    </div>
  );
}

function StoryExperience({ story, scene }) {
  const [begun, setBegun] = useState(false);

  if (!story) return null;

  if (!begun) {
    return (
      <div className="modal-scrim story-intro-scrim">
        <section className="story-intro panel-glass" role="dialog" aria-labelledby="story-title">
          <Badge tone="sand">YOUR STORY MISSION</Badge>
          <h2 id="story-title">{story.title}</h2>
          <p>{story.introduction}</p>
          <div className="story-intro-detail"><b>The world</b><span>{story.background}</span></div>
          <div className="story-intro-detail"><b>Your character</b><span>{story.main_character}</span></div>
          <div className="story-intro-detail"><b>The challenge</b><span>{story.problem}</span></div>
          <div className="story-mission-summary">
            <Sparkles size={16} />
            <span><b>{story.mission.title}</b><small>{story.mission.objectives[0]?.title || story.mission.final_challenge}</small></span>
          </div>
          <button className="primary-button modal-action" onClick={() => setBegun(true)}><Play size={16} fill="currentColor" /> Begin mission</button>
        </section>
      </div>
    );
  }

  const dialogue = scene?.dialogues?.[0];
  return (
    <aside className="story-beat panel-glass" aria-live="polite">
      <div className="story-beat-heading"><Badge>STORY SCENE</Badge><span>{scene?.name || "Mission briefing"}</span></div>
      <p>{scene?.description || story.background}</p>
      {dialogue && <blockquote><b>{dialogue.character}</b><span>{dialogue.text}</span></blockquote>}
      <small className="story-mission-label"><Sparkles size={13} /> {story.mission.title}</small>
    </aside>
  );
}

function ActivityWorkspace({ player, room, activity, stepIndex, currentStep, busy, error, result, quiz, answers, setAnswers, quizResult, onSubmitQuiz, onRetryQuiz, carriedItem, placedItems, onAction, onBack, story, storyScene, storyEnding }) {
  const [amount, setAmount] = useState(10);
  const [reading, setReading] = useState("");
  const [draggedItem, setDraggedItem] = useState("");
  const items = activity.simulation?.items || [];
  const unitReading = currentStep?.unit && ["measure", "weigh"].includes(currentStep.action);

  const runCurrentStep = () => {
    if (!currentStep) return;
    if (currentStep.action === "pick") onAction("pick", { item: currentStep.item });
    else if (currentStep.action === "place") onAction("place", { item: currentStep.item, target: "workbench" });
    else if (currentStep.action === "pour") onAction("pour", { item: currentStep.item, millilitres: Number(amount) });
    else if (currentStep.action === "mix") onAction("mix", { method: currentStep.method || "swirl" });
    else if (["measure", "weigh", "calculate"].includes(currentStep.action)) {
      onAction(currentStep.action, { value: Number(reading), unit: currentStep.unit });
      setReading("");
    } else {
      onAction(currentStep.action, { item: currentStep.item, completed: true });
    }
  };

  const onInventoryDrop = (event) => {
    event.preventDefault();
    const item = event.dataTransfer.getData("text/eduplay-item") || draggedItem;
    if (item && currentStep?.action === "pick" && item === currentStep.item) {
      onAction("pick", { item });
      setDraggedItem("");
    }
  };
  const onBenchDrop = (event) => {
    event.preventDefault();
    const item = event.dataTransfer.getData("text/eduplay-item") || draggedItem || carriedItem;
    if (item && currentStep?.action === "place" && item === currentStep.item) {
      onAction("place", { item, target: "workbench" });
      setDraggedItem("");
    }
  };
  const onWorldDrop = (event) => {
    event.preventDefault();
    const item = event.dataTransfer.getData("text/eduplay-item") || draggedItem || carriedItem;
    if (item !== currentStep?.item) return;
    if (currentStep.action === "pick") onAction("pick", { item });
    else if (currentStep.action === "place" && item === carriedItem) onAction("place", { item, target: "workbench" });
    setDraggedItem("");
  };
  const allowWorldDrop = (event) => {
    if (Array.from(event.dataTransfer.types).includes("text/eduplay-item")) event.preventDefault();
  };

  return (
    <div className="activity-room-screen">
      <div className="learning-room-world" onDragOver={allowWorldDrop} onDrop={onWorldDrop}><Suspense fallback={<div className="world-loading">Loading the learning room…</div>}><LearningRoomWorld name={room.name} roomType={room.room_type} activity={activity} currentStep={currentStep} carriedItem={carriedItem} placedItems={placedItems} stepIndex={stepIndex} /></Suspense></div>
      <header className="lab-topbar">
        <button className="room-back" onClick={onBack}><ArrowLeft size={16} /><span>ROOM</span></button>
        <div className="lab-brand"><div className="brand-mark"><Hand size={17} /></div><span>EDU<span>PLAY</span></span><i>/</i><span>INTERACTIVE ACTIVITY</span></div>
        <div className="lab-location"><span className="live-dot" /> CLASS {player.class}</div>
      </header>
      <aside className="activity-sidebar panel-glass">
        <div className="room-kicker"><Badge>{activity.activity_type}</Badge><span>{Math.min(stepIndex + (result ? 0 : 1), activity.steps_count)} / {activity.steps_count}</span></div>
        <h1>{activity.title}</h1>
        <p className="room-intro">{activity.objective}</p>
        <div className="activity-step-count"><span style={{ width: `${(stepIndex / activity.steps_count) * 100}%` }} /></div>
        <div className="active-instruction"><span>NEXT STEP</span><p>{currentStep?.instruction || "All steps complete!"}</p></div>
        {!result && currentStep && (
          <div className="activity-task-card">
            {["pick", "place"].includes(currentStep.action) && (
              <>
                <div className="task-card-title"><Hand size={16} /> {currentStep.action === "pick" ? "Pick up the item" : "Place it on the workbench"}</div>
                {currentStep.action === "pick" ? (
                  <>
                    <div className="activity-object-preview">
                      <span className="activity-object-preview-label">REQUESTED OBJECT</span>
                      <strong>{currentStep.item.replaceAll("-", " ")}</strong>
                      <span className="activity-object-preview-title">{activity.title}</span>
                      <p>{activity.objective}</p>
                    </div>
                    <div className="activity-inventory">
                      {items.map((item) => <button
                        key={item}
                        draggable={item === currentStep.item && !busy}
                        className={`inventory-item ${item === currentStep.item ? "inventory-target" : ""}`}
                        onDragStart={(event) => {
                          if (item !== currentStep.item) {
                            event.preventDefault();
                            return;
                          }
                          setDraggedItem(item);
                          event.dataTransfer.effectAllowed = "move";
                          event.dataTransfer.setData("text/eduplay-item", item);
                        }}
                        onClick={() => item === currentStep.item && runCurrentStep()}
                        aria-label={`${item.replaceAll("-", " ")}${item === currentStep.item ? ", requested object, click or drag to pick up" : ""}`}
                      >
                        <strong>{item.replaceAll("-", " ")}</strong>
                        {item === currentStep.item && <small>CLICK OR DRAG TO PICK UP</small>}
                      </button>)}
                    </div>
                    <button className="activity-drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={onInventoryDrop} onClick={runCurrentStep}>
                      <Hand size={16} /><span><strong>Pick up {currentStep.item.replaceAll("-", " ")}</strong><small>Drop it here or drag it into the 3D workspace</small></span>
                    </button>
                  </>
                ) : (
                  <>
                    <div className="activity-object-preview activity-object-held">
                      <span className="activity-object-preview-label">OBJECT IN HAND</span>
                      <strong>{currentStep.item.replaceAll("-", " ")}</strong>
                      <span className="activity-object-preview-title">Drag it to the workbench</span>
                    </div>
                    <div className="activity-workbench" onDragOver={(event) => event.preventDefault()} onDrop={onBenchDrop}>
                      {[...new Set([...placedItems, carriedItem].filter(Boolean))].map((item) => (
                        <button
                          className={`placed-item ${item === carriedItem ? "placed-item-carried" : ""}`}
                          key={item}
                          draggable={item === carriedItem && !busy}
                          onDragStart={(event) => {
                            setDraggedItem(item);
                            event.dataTransfer.effectAllowed = "move";
                            event.dataTransfer.setData("text/eduplay-item", item);
                          }}
                          onClick={() => item === carriedItem && runCurrentStep()}
                        >
                          <BookOpen size={14} />{item.replaceAll("-", " ")}
                          {item === carriedItem && <small>DRAG TO PLACE</small>}
                        </button>
                      ))}
                      {!carriedItem && <span className="workbench-instruction">Pick up {currentStep.item.replaceAll("-", " ")} to place it here</span>}
                    </div>
                    <button className="activity-drop-zone activity-place-zone" onDragOver={(event) => event.preventDefault()} onDrop={onBenchDrop} onClick={runCurrentStep} disabled={busy || carriedItem !== currentStep.item}>
                      <BookOpen size={16} /><span><strong>Place on workbench</strong><small>Drop the held object here or into the 3D workspace</small></span>
                    </button>
                  </>
                )}
              </>
            )}
            {currentStep.action === "pour" && (
              <>
                <div className="task-card-title"><FlaskConical size={16} /> Measure and pour</div>
                <label className="activity-input-label">Virtual volume <output>{amount} mL</output><input type="range" min="1" max="25" value={amount} onChange={(event) => setAmount(Number(event.target.value))} /></label>
                <button className="primary-button action-button" disabled={busy} onClick={runCurrentStep}>Pour into the container <ArrowRight size={14} /></button>
              </>
            )}
            {currentStep.action === "mix" && (
              <>
                <div className="task-card-title"><Sparkles size={16} /> Mix the virtual sample</div>
                <div className="mixing-control"><span>BEAKER</span><span className="mixing-liquid" /><span>GENTLE SWIRL</span></div>
                <button className="primary-button action-button" disabled={busy} onClick={runCurrentStep}>Swirl to mix <ArrowRight size={14} /></button>
              </>
            )}
            {["measure", "weigh", "calculate"].includes(currentStep.action) && (
              <>
                <div className="task-card-title"><Scale size={16} /> {currentStep.action === "weigh" ? "Use the virtual balance" : currentStep.action === "calculate" ? "Enter your calculation" : "Read the virtual instrument"}</div>
                {unitReading && <div className="virtual-instrument"><span>{currentStep.action === "weigh" ? "DIGITAL BALANCE" : "MEASUREMENT"}</span><strong>{currentStep.action === "weigh" ? "10.0" : "10"} <i>{currentStep.unit}</i></strong></div>}
                <label className="activity-input-label">Enter your reading<input className="activity-number-input" type="number" step="any" value={reading} onChange={(event) => setReading(event.target.value)} placeholder={currentStep.unit || "Answer"} /></label>
                <button className="primary-button action-button" disabled={busy || reading === ""} onClick={runCurrentStep}>Record reading <ArrowRight size={14} /></button>
              </>
            )}
            {!["pick", "place", "pour", "mix", "measure", "weigh", "calculate"].includes(currentStep.action) && (
              <>
                <div className="task-card-title"><BookOpen size={16} /> Complete this action</div>
                <div className="activity-workbench activity-workspace"><span>{currentStep.item?.replaceAll("-", " ") || "Your workspace"}</span><span className="workspace-dots">● ● ●</span></div>
                <button className="primary-button action-button" disabled={busy} onClick={runCurrentStep}>Complete this step <ArrowRight size={14} /></button>
              </>
            )}
          </div>
        )}
        {result && (
          <div className="activity-complete">
            <div className="quiz-complete-icon"><Trophy size={22} /></div>
            <h2>{quizResult ? "Activity complete!" : "Activity steps complete!"}</h2>
            <p>You worked through every guided step in {activity.title}.</p>
            {!quizResult && !quiz.length && <button className="primary-button room-start-button" disabled={busy} onClick={onRetryQuiz}>Load activity quiz <ArrowRight size={14} /></button>}
          </div>
        )}
        {error && <div className="notice notice-error room-error">{error}</div>}
      </aside>
      <div className="room-scene-caption panel-glass"><span className="scene-dot" /> STEP {Math.min(stepIndex + (result ? 0 : 1), activity.steps_count)} <i>·</i> {currentStep ? `${currentStep.action.toUpperCase()}${currentStep.item ? ` · ${currentStep.item.replaceAll("-", " ").toUpperCase()}` : ""}` : "COMPLETE"}</div>
      <StoryExperience story={story} scene={storyScene} />
      {result && quiz.length > 0 && (
        <div className="quiz-overlay"><QuizPanel quiz={quiz} answers={answers} setAnswers={setAnswers} busy={busy} result={quizResult} onSubmit={onSubmitQuiz} onReturn={onBack} assessmentLabel="ACTIVITY" ending={storyEnding} /></div>
      )}
    </div>
  );
}

function QuizPanel({ quiz, answers, setAnswers, busy, result, onSubmit, onReturn, assessmentLabel = "PRACTICAL", ending }) {
  if (result) {
    return (
      <section className="quiz-panel panel-glass">
        <div className="quiz-complete-icon"><Trophy size={24} /></div>
        <Badge tone="sand">{assessmentLabel} COMPLETE</Badge>
        <h2>{result.score >= 80 ? "Brilliant work!" : "Experiment complete!"}</h2>
        <p className="quiz-score">{result.score}<small>%</small></p>
        <span className="score-caption">{result.correct_count} of {result.total_questions} answers correct</span>
        {ending && <div className="story-ending"><Badge tone="sand">STORY RESOLVED</Badge><b>{ending.name}</b><p>{ending.description}</p>{ending.dialogues?.map((dialogue, index) => <p key={`${dialogue.character}-${index}`}><strong>{dialogue.character}:</strong> {dialogue.text}</p>)}</div>}
        <div className="reward-row">
          <div><Star size={17} /><strong>+{result.reward.xp}</strong><small>XP earned</small></div>
          <div><Coins size={17} /><strong>+{result.reward.coins}</strong><small>coins</small></div>
        </div>
        <div className="quiz-feedback">
          {result.results.map((item) => (
            <div key={item.question_id} className={item.correct ? "feedback-correct" : "feedback-missed"}>
              <span>{item.correct ? "✓" : "↗"}</span><p><b>{item.difficulty}</b> · {item.explanation}</p>
            </div>
          ))}
        </div>
        <button className="primary-button modal-action" onClick={onReturn}>Return to campus <ArrowRight size={17} /></button>
      </section>
    );
  }

  return (
    <section className="quiz-panel panel-glass">
      <div className="quiz-heading">
        <Badge tone="sand">KNOWLEDGE CHECK</Badge>
        <span>{quiz.length} LEVELS <i>·</i> {quiz.length} QUESTIONS</span>
      </div>
      <h2>Show what you discovered</h2>
      <p className="quiz-intro">Answer each question to complete this learning check and collect your rewards.</p>
      <div className="quiz-question-list">
        {quiz.map((question, index) => (
          <article className="quiz-question" key={question.id}>
            <div className="question-top"><span>0{index + 1}</span><Badge tone={index === 0 ? "mint" : index === 1 ? "blue" : "rose"}>{question.difficulty}</Badge></div>
            <h3>{question.prompt}</h3>
            <div className="answer-options">
              {question.options.map((option, optionIndex) => (
                <button
                  key={option}
                  className={answers[index] === optionIndex ? "answer-option selected" : "answer-option"}
                  onClick={() => setAnswers((current) => current.map((value, answerIndex) => answerIndex === index ? optionIndex : value))}
                >
                  <span>{String.fromCharCode(65 + optionIndex)}</span>{option}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
      <div className="quiz-footer">
        <span><Sparkles size={14} /> Complete the quiz to earn learning rewards</span>
        <button className="primary-button" disabled={busy || answers.some((answer) => answer === null)} onClick={onSubmit}>
          {busy ? "Checking…" : "Submit answers"} <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
}

function LabWorkspace({ player, practical, stepIndex, selectedSample, result, onSelectSample, onAction, busy, error, quiz, answers, setAnswers, quizResult, onSubmitQuiz, onReturn, onAssistant, story, storyScene, storyEnding }) {
  const [ph, setPh] = useState("7");
  const [category, setCategory] = useState("neutral");
  const [pourAmount, setPourAmount] = useState(10);
  const [collectedItems, setCollectedItems] = useState([]);
  const [draggedEquipment, setDraggedEquipment] = useState("");
  const [question, setQuestion] = useState("");
  const [assistantReply, setAssistantReply] = useState("");
  const [assistantBusy, setAssistantBusy] = useState(false);
  const [showAssistant, setShowAssistant] = useState(false);
  const [showNotebook, setShowNotebook] = useState(false);
  const currentStep = practical.steps[stepIndex];

  useEffect(() => {
    if (result) {
      setPh(String(result.ph));
      setCategory(result.category);
    }
  }, [result]);

  const askAssistant = async (event) => {
    event.preventDefault();
    if (!question.trim()) return;
    setAssistantBusy(true);
    try {
      const response = await onAssistant(question);
      setAssistantReply(response.answer);
    } catch (requestError) {
      setAssistantReply(`The learning assistant is unavailable: ${requestError.message}`);
    } finally {
      setAssistantBusy(false);
    }
  };

  const submitObservation = () => onAction("record_observation", { ph: Number(ph), category });
  const placeOnBench = (item) => onAction("place_object", { item, target: "workbench" });
  const dropEquipment = (event) => {
    event.preventDefault();
    const item = event.dataTransfer.getData("text/lab-equipment") || draggedEquipment;
    if (item && currentStep?.action === "collect_equipment" && !collectedItems.includes(item)) {
      setCollectedItems((items) => [...items, item]);
    }
    if (item && currentStep?.action === "place_object" && currentStep.equipment?.some((equipment) => equipment.slug === item)) {
      placeOnBench(item);
    }
  };

  return (
    <div className="lab-screen">
      <div className="lab-world"><Suspense fallback={<div className="world-loading">Loading laboratory…</div>}><LabWorld selectedSample={selectedSample} result={result} /></Suspense></div>
      <header className="lab-topbar">
        <div className="lab-brand"><div className="brand-mark"><Atom size={18} /></div><span>EDU<span>PLAY</span></span><i>/</i><span>SCIENCE BLOCK</span></div>
        <div className="lab-location"><span className="live-dot" /> CHEMISTRY LAB <i>·</i> CLASS {player.class}</div>
        <div className="lab-top-actions"><button className="notebook-button" onClick={() => setShowNotebook((value) => !value)}><BookOpen size={16} /> Notebook</button><button className="icon-button" title="Ask the learning assistant" onClick={() => setShowAssistant((value) => !value)}><BrainCircuit size={17} /></button></div>
      </header>

      <aside className="lab-sidebar panel-glass">
        <div className="lab-sidebar-kicker"><Badge>VIRTUAL PRACTICAL</Badge><span>01 / 01</span></div>
        <h1>{practical.title}</h1>
        <p className="lab-chapter">{practical.chapter}</p>
        <div className="objective-box"><span>YOUR MISSION</span><p>{practical.objective}</p></div>
        <div className="step-progress">
          {practical.steps.slice(0, stepIndex).map((step, index) => (
            <div key={step.order} className="step-line step-done">
              <span className="step-marker"><BadgeCheck size={14} /></span>
              <span>{index + 1}. Completed</span>
            </div>
          ))}
          {currentStep && (
            <div className="step-line step-current">
              <span className="step-marker">{String(stepIndex + 1).padStart(2, "0")}</span>
              <span>{currentStep.instruction}</span>
            </div>
          )}
        </div>

        {currentStep?.action === "collect_equipment" && (
          <div className="task-card">
            <div className="task-card-title"><ShieldCheck size={16} /> Pick up each virtual instrument</div>
            <div className="equipment-list">
              {currentStep.equipment.map((item, index) => (
                <button
                  key={item.slug}
                  draggable
                  className={`equipment-chip equipment-pick ${collectedItems.includes(item.slug) ? "equipment-collected" : ""}`}
                  onDragStart={(event) => { setDraggedEquipment(item.slug); event.dataTransfer.setData("text/lab-equipment", item.slug); }}
                  onClick={() => setCollectedItems((items) => items.includes(item.slug) ? items : [...items, item.slug])}
                ><i>{["◈", "▱", "⌁", "▤", "◯", "⌁", "▥"][index]}</i>{item.name}{collectedItems.includes(item.slug) && <BadgeCheck size={12} />}</button>
              ))}
            </div>
            <button className="activity-drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={dropEquipment}><Hand size={14} /> Drag instruments into your kit or tap each one</button>
            <button className="primary-button action-button" disabled={busy || currentStep.equipment.some((item) => !collectedItems.includes(item.slug))} onClick={() => onAction("collect_equipment", { equipment: collectedItems })}>
              <BadgeCheck size={15} /> Collect selected instruments
            </button>
          </div>
        )}

        {currentStep?.action === "place_object" && (
          <div className="task-card">
            <div className="task-card-title"><Hand size={16} /> Put the instrument on the workbench</div>
            <div className="lab-workbench-drop" onDragOver={(event) => event.preventDefault()} onDrop={dropEquipment}>
              <span>VIRTUAL WORKBENCH</span><strong>{currentStep.equipment.map((item) => item.name).join(" / ")}</strong>
              <small>Drag the instrument here or tap to place it</small>
            </div>
            <div className="equipment-list">
              {currentStep.equipment.map((item) => <button key={item.slug} className="equipment-chip equipment-pick" disabled={!collectedItems.includes(item.slug) || busy} draggable={collectedItems.includes(item.slug)} onDragStart={(event) => { setDraggedEquipment(item.slug); event.dataTransfer.setData("text/lab-equipment", item.slug); }} onClick={() => placeOnBench(item.slug)}>{item.name}</button>)}
            </div>
          </div>
        )}

        {currentStep?.action === "choose_sample" && (
          <div className="task-card">
            <div className="task-card-title"><FlaskConical size={16} /> Choose a virtual sample</div>
            <div className="sample-list">
              {practical.samples.map((sample) => (
                <button className={`sample-option ${selectedSample === sample.slug ? "sample-selected" : ""}`} key={sample.slug} onClick={() => onSelectSample(sample.slug)}>
                  <span className={`sample-liquid sample-${sample.slug}`} /><span>{sample.name}</span>
                  {selectedSample === sample.slug && <BadgeCheck size={15} />}
                </button>
              ))}
            </div>
            <button className="primary-button action-button" disabled={busy || !selectedSample} onClick={() => onAction("choose_sample", { sample: selectedSample })}>Select sample <ArrowRight size={15} /></button>
          </div>
        )}

        {currentStep?.action === "test_indicator" && (
          <div className="task-card">
            <div className="task-card-title"><Sparkles size={16} /> Run the virtual test</div>
            <p className="task-hint">Use the paper strip on the sample. Compare its colour with the pH chart.</p>
            <div className="mini-ph-chart"><span>ACID</span><div /><span>NEUTRAL</span><div /><span>BASE</span></div>
            <button className="primary-button action-button" disabled={busy} onClick={() => onAction("test_indicator", {})}><FlaskConical size={15} /> Test indicator</button>
          </div>
        )}

        {currentStep?.action === "pour_liquid" && (
          <div className="task-card">
            <div className="task-card-title"><FlaskConical size={16} /> Measure and pour the sample</div>
            <label className="activity-input-label">Virtual volume <output>{pourAmount} mL</output><input type="range" min="1" max="25" value={pourAmount} onChange={(event) => setPourAmount(Number(event.target.value))} /></label>
            <button className="primary-button action-button" disabled={busy} onClick={() => onAction("pour_liquid", { millilitres: pourAmount })}>Pour into the test tube <ArrowRight size={14} /></button>
          </div>
        )}

        {currentStep?.action === "mix" && (
          <div className="task-card">
            <div className="task-card-title"><Sparkles size={16} /> Mix the virtual sample</div>
            <div className="mixing-control"><span>TEST TUBE</span><span className="mixing-liquid" /><span>GENTLE SWIRL</span></div>
            <button className="primary-button action-button" disabled={busy} onClick={() => onAction("mix", { method: "swirl" })}>Gently swirl to mix <ArrowRight size={14} /></button>
          </div>
        )}

        {currentStep?.action === "measure_ph" && result && (
          <div className="task-card">
            <div className="task-card-title"><Scale size={16} /> Read the indicator chart</div>
            <div className="observation-result"><span className="result-swatch" style={{ backgroundColor: result.color }} /><span>Compare the colour and enter its pH.</span></div>
            <label className="activity-input-label">pH reading<select value={ph} onChange={(event) => setPh(event.target.value)}>{Array.from({ length: 14 }, (_, index) => index + 1).map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <button className="primary-button action-button" disabled={busy} onClick={() => onAction("measure_ph", { ph: Number(ph) })}>Measure pH <ArrowRight size={14} /></button>
          </div>
        )}

        {currentStep?.action === "record_observation" && result && (
          <div className="task-card">
            <div className="task-card-title"><BookOpen size={16} /> Record in your notebook</div>
            <div className="observation-result">
              <span className="result-swatch" style={{ backgroundColor: result.color }} />
              <span>Indicator changed to <b>{result.category}</b></span>
            </div>
            <div className="observation-selects">
              <label>pH reading<select value={ph} onChange={(event) => setPh(event.target.value)}>{Array.from({ length: 14 }, (_, index) => index + 1).map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
              <label>Classification<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="acidic">Acidic</option><option value="neutral">Neutral</option><option value="basic">Basic</option></select></label>
            </div>
            <button className="primary-button action-button" disabled={busy} onClick={submitObservation}>Save observation <ArrowRight size={15} /></button>
          </div>
        )}

        {stepIndex >= practical.steps.length && (
          <div className="task-card">
            <div className="task-card-title"><BadgeCheck size={16} /> Practical observations saved</div>
            <p className="task-hint">Your experiment is ready for its knowledge check.</p>
          </div>
        )}
        {error && <div className="notice notice-error lab-error"><CircleHelp size={15} />{error}</div>}
        <div className="lab-safety"><ShieldCheck size={14} /><span>{practical.safety_information}</span></div>
      </aside>

      <div className="lab-scene-caption panel-glass"><span className="scene-dot" /> INTERACTIVE LABORATORY <i>·</i> DRAG TO LOOK AROUND</div>
      <StoryExperience story={story} scene={storyScene} />
      {showNotebook && (
        <div className="floating-notebook panel-glass">
          <button className="icon-button note-close" onClick={() => setShowNotebook(false)} aria-label="Close notebook"><X size={16} /></button>
          <Badge tone="sand">FIELD NOTES</Badge><h3>Experiment notebook</h3>
          <p><b>Objective</b><br />{practical.objective}</p>
          <p><b>Sample</b><br />{practical.samples.find((sample) => sample.slug === selectedSample)?.name || "Not selected yet"}</p>
          <p><b>Observation</b><br />{result ? `pH ${result.ph} · ${result.category}` : "Complete the virtual indicator test to record an observation."}</p>
        </div>
      )}
      {showAssistant && (
        <div className="assistant-card panel-glass">
          <button className="icon-button note-close" onClick={() => setShowAssistant(false)} aria-label="Close assistant"><X size={16} /></button>
          <div className="assistant-title"><span><BrainCircuit size={17} /></span><div><b>Learning companion</b><small>Curriculum-aware · offline guide</small></div></div>
          <div className="assistant-answer">{assistantReply || "Need a hint? Ask me about pH, acids, bases, or the indicator."}</div>
          <form onSubmit={askAssistant} className="assistant-form"><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question…" /><button className="icon-button" disabled={assistantBusy} aria-label="Send question"><ArrowRight size={16} /></button></form>
        </div>
      )}
      {stepIndex >= practical.steps.length && quiz.length > 0 && (
        <div className="quiz-overlay"><QuizPanel quiz={quiz} answers={answers} setAnswers={setAnswers} busy={busy} result={quizResult} onSubmit={onSubmitQuiz} onReturn={onReturn} ending={storyEnding} /></div>
      )}
    </div>
  );
}

function ProgressModal({ data, onClose, loading, error }) {
  return (
    <div className="modal-scrim">
      <section className="progress-modal panel-glass">
        <button className="icon-button modal-close" aria-label="Close progress" onClick={onClose}><X size={17} /></button>
        <Badge tone="sand">YOUR LEARNING JOURNEY</Badge>
        <h2>Progress & achievements</h2>
        {loading && <div className="progress-loading"><span className="spinner-border spinner-border-sm" /> Loading progress…</div>}
        {error && <div className="notice notice-error">{error}</div>}
        {data && (
          <>
            <div className="progress-summary">
              <div><Star size={17} /><strong>{data.player.xp}</strong><span>XP</span></div>
              <div><Coins size={17} /><strong>{data.player.coins}</strong><span>Coins</span></div>
              <div><BadgeCheck size={17} /><strong>{data.completed_practicals}</strong><span>Practicals</span></div>
            </div>
            <div className="progress-list">
              <h3>RECENT ACTIVITY</h3>
              {data.attempts.length ? data.attempts.map((attempt) => (
                <div className="progress-attempt" key={attempt.attempt_id}><div><b>{attempt.practical}</b><span>Score {attempt.score}%</span></div><Badge tone="mint">+{attempt.xp} XP</Badge></div>
              )) : <p>Your completed practicals will appear here.</p>}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

export default function App() {
  const [screen, setScreen] = useState("welcome");
  const [name, setName] = useState("Alex");
  const [selectedClass, setSelectedClass] = useState(10);
  const [classes, setClasses] = useState(INITIAL_CLASSES);
  const [learner, setLearner] = useState(null);
  const [curriculum, setCurriculum] = useState(null);
  const [practicals, setPracticals] = useState([]);
  const [roomData, setRoomData] = useState(null);
  const [roomLoading, setRoomLoading] = useState(false);
  const [activePractical, setActivePractical] = useState(null);
  const [attemptId, setAttemptId] = useState(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [selectedSample, setSelectedSample] = useState("");
  const [testResult, setTestResult] = useState(null);
  const [quiz, setQuiz] = useState([]);
  const [answers, setAnswers] = useState([null, null, null]);
  const [quizResult, setQuizResult] = useState(null);
  const [activeActivity, setActiveActivity] = useState(null);
  const [activityAttemptId, setActivityAttemptId] = useState(null);
  const [activityStep, setActivityStep] = useState(null);
  const [activityStepIndex, setActivityStepIndex] = useState(0);
  const [activityResult, setActivityResult] = useState(null);
  const [activityQuiz, setActivityQuiz] = useState([]);
  const [activityAnswers, setActivityAnswers] = useState([]);
  const [activityQuizResult, setActivityQuizResult] = useState(null);
  const [activeStory, setActiveStory] = useState(null);
  const [storyScene, setStoryScene] = useState(null);
  const [storyEnding, setStoryEnding] = useState(null);
  const [carriedItem, setCarriedItem] = useState("");
  const [placedItems, setPlacedItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [error, setError] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [nearBuilding, setNearBuilding] = useState(null);
  const [paused, setPaused] = useState(false);
  const [progressOpen, setProgressOpen] = useState(false);
  const [progress, setProgress] = useState(null);
  const [progressLoading, setProgressLoading] = useState(false);
  const [progressError, setProgressError] = useState("");
  const [supabaseUser, setSupabaseUser] = useState(null);

  useEffect(() => {
    if (!supabase) return undefined;
    supabase.auth.getSession().then(({ data }) => setSupabaseUser(data.session?.user || null));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => setSupabaseUser(session?.user || null));
    return () => listener.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    api(`/curriculum/?class=${selectedClass}`)
      .then((data) => {
        setCurriculum(data);
        setClasses(data.classes);
      })
      .catch((requestError) => setError(`Could not load curriculum: ${requestError.message}`));
  }, [selectedClass]);

  useEffect(() => {
    const keydown = (event) => {
      if (event.code === "Escape" && screen === "campus" && !progressOpen) {
        setPaused((value) => !value);
      }
    };
    window.addEventListener("keydown", keydown);
    return () => window.removeEventListener("keydown", keydown);
  }, [screen, progressOpen]);

  const startJourney = async () => {
    setLoadingProfile(true);
    setError("");
    try {
      const profile = await api("/players/", { method: "POST", body: withGuestId({ display_name: name.trim(), class: selectedClass }) });
      setLearner(profile);
      setScreen("campus");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoadingProfile(false);
    }
  };

  const authenticate = async (mode, email, password) => {
    if (!supabase) return;
    setAuthBusy(true);
    setAuthMessage("");
    try {
      const result = mode === "signup"
        ? await supabase.auth.signUp({ email, password })
        : await supabase.auth.signInWithPassword({ email, password });
      if (result.error) throw result.error;
      if (mode === "signup" && !result.data.session) {
        setAuthMessage("Account created. Check your email to confirm it, then log in.");
      } else {
        setAuthMessage("Account connected. Enter the campus when you're ready.");
      }
    } catch (authError) {
      setAuthMessage(authError.message || "Could not connect to Supabase Auth.");
    } finally {
      setAuthBusy(false);
    }
  };

  const enterRoom = useCallback(async (roomSlug) => {
    if (!learner) return;
    setRoomLoading(true);
    setNearBuilding(null);
    setError("");
    setScreen("room");
    try {
      const room = await api(`/rooms/${learner.class}/${roomSlug}/`);
      setRoomData(room);
      setPracticals([]);
      if (roomSlug === "science") {
        const response = await api(`/practicals/?class=${learner.class}&subject=${roomSlug}`);
        setPracticals(response.practicals);
      }
    } catch (requestError) {
      setRoomData(null);
      setError(requestError.message);
    } finally {
      setRoomLoading(false);
    }
  }, [learner]);

  const openNearbyRoom = useCallback(() => {
    if (nearBuilding && screen === "campus") enterRoom(nearBuilding.id);
  }, [nearBuilding, screen, enterRoom]);

  const enterLab = async (practical) => {
    setBusy(true);
    setError("");
    try {
      const response = await api("/attempts/", { method: "POST", body: withGuestId({ practical_slug: practical.slug }) });
      setActivePractical(response.practical);
      setActiveStory(response.story || null);
      setStoryScene(response.story?.scenes?.[0] || null);
      setStoryEnding(null);
      setAttemptId(response.attempt_id);
      setStepIndex(0);
      setSelectedSample("");
      setTestResult(null);
      setQuiz([]);
      setAnswers([null, null, null]);
      setQuizResult(null);
      setScreen("lab");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const startActivity = async (activity) => {
    setBusy(true);
    setError("");
    try {
      const response = await api("/activities/start/", {
        method: "POST",
        body: withGuestId({ activity_slug: activity.slug }),
      });
      setActiveActivity(response.activity);
      setActiveStory(response.story || null);
      setStoryScene(response.story?.scenes?.[0] || null);
      setStoryEnding(null);
      setActivityAttemptId(response.attempt_id);
      setActivityStep(response.current_step);
      setActivityStepIndex(0);
      setActivityResult(null);
      setActivityQuiz([]);
      setActivityAnswers([]);
      setActivityQuizResult(null);
      setCarriedItem("");
      setPlacedItems([]);
      setScreen("activity");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const loadActivityQuiz = async (attemptId = activityAttemptId) => {
    if (!attemptId) return;
    setError("");
    try {
      const quizData = await api(`/activity-attempts/${attemptId}/quiz/?player_id=${getGuestId()}`);
      setActivityQuiz(quizData.questions);
      setActivityAnswers(quizData.questions.map(() => null));
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  const runActivityAction = async (action, payload) => {
    if (!activityAttemptId) return;
    setBusy(true);
    setError("");
    try {
      const response = await api(`/activity-attempts/${activityAttemptId}/action/`, {
        method: "POST",
        body: withGuestId({ action, payload }),
      });
      if (action === "pick") setCarriedItem(payload.item);
      if (action === "place") {
        setCarriedItem("");
        setPlacedItems((current) => current.includes(payload.item) ? current : [...current, payload.item]);
      }
      if (response.story_scene) setStoryScene(response.story_scene);
      setActivityStepIndex(response.step_index);
      setActivityStep(response.current_step || null);
      if (response.status === "quiz") {
        setActivityResult(response);
        await loadActivityQuiz(activityAttemptId);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const submitActivityQuiz = async () => {
    if (!activityAttemptId) return;
    setBusy(true);
    setError("");
    try {
      const response = await api(`/activity-attempts/${activityAttemptId}/quiz/`, {
        method: "POST",
        body: withGuestId({
          answers: activityQuiz.map((question, index) => ({
            question_id: question.id,
            selected_option: activityAnswers[index],
          })),
        }),
      });
      setActivityQuizResult(response);
      setStoryEnding(response.story_ending || null);
      setLearner(response.player);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const runAction = async (action, payload) => {
    if (!attemptId) return;
    setBusy(true);
    setError("");
    try {
      const response = await api(`/attempts/${attemptId}/action/`, {
        method: "POST",
        body: withGuestId({ action, payload }),
      });
      if (response.result) setTestResult(response.result);
      if (response.story_scene) setStoryScene(response.story_scene);
      setStepIndex(response.step_index);
      if (response.status === "quiz") {
        const quizData = await api(`/attempts/${attemptId}/quiz/?player_id=${getGuestId()}`);
        setQuiz(quizData.questions);
        setAnswers(quizData.questions.map(() => null));
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const submitQuiz = async () => {
    setBusy(true);
    setError("");
    try {
      const response = await api(`/attempts/${attemptId}/quiz/`, {
        method: "POST",
        body: withGuestId({
          answers: quiz.map((question, index) => ({ question_id: question.id, selected_option: answers[index] })),
        }),
      });
      setQuizResult(response);
      setStoryEnding(response.story_ending || null);
      setLearner(response.player);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const loadProgress = async () => {
    if (!learner) return;
    setProgressOpen(true);
    setProgressLoading(true);
    setProgressError("");
    try {
      const data = await api(`/progress/?player_id=${getGuestId()}`);
      setProgress(data);
    } catch (requestError) {
      setProgressError(requestError.message);
    } finally {
      setProgressLoading(false);
    }
  };

  const askAssistant = async (question) => api("/assistant/", { method: "POST", body: { question, class: learner?.class, chapter: activePractical?.chapter } });

  const returnToRoom = () => {
    setScreen("room");
    setActivePractical(null);
    setAttemptId(null);
    setActiveActivity(null);
    setActivityAttemptId(null);
    setActivityStep(null);
    setActivityResult(null);
    setActivityQuiz([]);
    setActivityQuizResult(null);
    setQuizResult(null);
    setActiveStory(null);
    setStoryScene(null);
    setStoryEnding(null);
    setError("");
  };

  const returnToCampus = () => {
    setScreen("campus");
    setPaused(false);
    setNearBuilding(null);
    setRoomData(null);
    setActivePractical(null);
    setAttemptId(null);
    setActiveActivity(null);
    setActivityAttemptId(null);
    setActivityStep(null);
    setActivityResult(null);
    setActivityQuiz([]);
    setActivityQuizResult(null);
    setQuizResult(null);
    setActiveStory(null);
    setStoryScene(null);
    setStoryEnding(null);
    setError("");
  };

  const levelProgress = useMemo(() => learner ? learner.xp % 100 : 0, [learner]);

  if (screen === "welcome") {
    return (
      <Welcome
        classes={classes}
        selectedClass={selectedClass}
        setSelectedClass={setSelectedClass}
        name={name}
        setName={setName}
        onStart={startJourney}
        loading={loadingProfile}
        error={error}
        authBusy={authBusy}
        onAuth={authenticate}
        onGuest={() => setSupabaseUser(null)}
        authMessage={authMessage}
      />
    );
  }

  if (screen === "lab" && learner && activePractical) {
    return (
      <LabWorkspace
        player={learner}
        practical={activePractical}
        stepIndex={stepIndex}
        selectedSample={selectedSample}
        result={testResult}
        onSelectSample={setSelectedSample}
        onAction={runAction}
        busy={busy}
        error={error}
        quiz={quiz}
        answers={answers}
        setAnswers={setAnswers}
        quizResult={quizResult}
        onSubmitQuiz={submitQuiz}
        onReturn={returnToRoom}
        onAssistant={askAssistant}
        story={activeStory}
        storyScene={storyScene}
        storyEnding={storyEnding}
      />
    );
  }

  if (screen === "room" && learner) {
    if (roomLoading) return <div className="world-loading room-loading">Entering your classroom…</div>;
    if (roomData) {
      return (
        <LearningRoom
          player={learner}
          room={roomData}
          practicals={practicals}
          busy={busy}
          error={error}
          onStartPractical={enterLab}
          onStartActivity={startActivity}
          onBack={returnToCampus}
          onOpenSubject={enterRoom}
        />
      );
    }
    return <div className="room-load-error"><p>{error || "Could not load this room."}</p><button className="primary-button" onClick={returnToCampus}>Back to campus</button></div>;
  }

  if (screen === "activity" && learner && roomData && activeActivity) {
    return (
      <ActivityWorkspace
        player={learner}
        room={roomData}
        activity={activeActivity}
        stepIndex={activityStepIndex}
        currentStep={activityStep}
        busy={busy}
        error={error}
        result={activityResult}
        quiz={activityQuiz}
        answers={activityAnswers}
        setAnswers={setActivityAnswers}
        quizResult={activityQuizResult}
        onSubmitQuiz={submitActivityQuiz}
        onRetryQuiz={loadActivityQuiz}
        carriedItem={carriedItem}
        placedItems={placedItems}
        onAction={runActivityAction}
        onBack={returnToRoom}
        story={activeStory}
        storyScene={storyScene}
        storyEnding={storyEnding}
      />
    );
  }

  return (
    <main className="game-screen">
      <div className="campus-canvas"><Suspense fallback={<div className="world-loading">Loading campus…</div>}><GameWorld subjects={curriculum?.subjects || []} onNearBuilding={setNearBuilding} onInteract={openNearbyRoom} paused={paused} /></Suspense></div>
      <div className="game-shade" />
      {learner && <PlayerCard player={learner} onProgress={loadProgress} />}
      <div className="campus-heading"><Badge>CLASS {learner?.class || selectedClass} CAMPUS</Badge><h1>A world of your own.</h1><p>Visit any subject room or the library to begin.</p></div>
      <div className="control-hint panel-glass"><span><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> Move</span><span><kbd>SHIFT</kbd> Run</span><span><kbd>SPACE</kbd> Jump</span><span><kbd>E</kbd> Enter room</span></div>
      {nearBuilding && !paused && (
        <button className="interact-prompt panel-glass" onClick={openNearbyRoom}>
          <span className="interact-key">E</span><span><strong>{nearBuilding.name}</strong><small>{nearBuilding.id === "library" ? "Browse books and class resources" : `Enter ${nearBuilding.subtitle}`}</small></span><ArrowRight size={18} />
        </button>
      )}
      <div className="campus-corner-actions">
        <div className="level-card panel-glass"><span>LEVEL {learner?.level || 1}</span><div><i style={{ width: `${levelProgress}%` }} /></div><small>{levelProgress} / 100 XP</small></div>
        <button className="icon-button pause-button panel-glass" onClick={() => setPaused(true)} aria-label="Pause game"><Pause size={18} /></button>
      </div>
      {error && <div className="campus-error notice notice-error">{error}<button onClick={() => setError("")}><X size={14} /></button></div>}
      {paused && (
        <div className="modal-scrim">
          <section className="pause-modal panel-glass">
            <button className="icon-button modal-close" aria-label="Close pause menu" onClick={() => setPaused(false)}><X size={17} /></button>
            <Badge tone="sand">TAKE A BREATHER</Badge><h2>Game paused</h2><p>Your progress is saved as you play.</p>
            <button className="primary-button modal-action" onClick={() => setPaused(false)}><Play size={16} fill="currentColor" /> Resume exploring</button>
            <button className="secondary-button modal-action" onClick={loadProgress}><Trophy size={16} /> View learning progress</button>
            {supabase && supabaseUser && <button className="text-button signout-button" onClick={() => supabase.auth.signOut()}><LogOut size={14} /> Log out</button>}
          </section>
        </div>
      )}
      {progressOpen && <ProgressModal data={progress} onClose={() => setProgressOpen(false)} loading={progressLoading} error={progressError} />}
      <div className="campus-brand"><div className="brand-mark"><Atom size={17} /></div><span>EDU<span>PLAY</span></span></div>
      <div className="campus-version"><LockKeyhole size={12} /> SAFE VIRTUAL WORLD</div>
      {curriculum && <span className="sr-only">Loaded curriculum for Class {curriculum.selected_class} with {curriculum.subjects.length} subjects.</span>}
    </main>
  );
}


import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./api.js", () => ({
  api: vi.fn(),
  getGuestId: () => "c1b503b3-d9ce-4a43-8736-58f8ef4ab529",
  supabase: null,
  withGuestId: (data) => ({ ...data, player_id: "c1b503b3-d9ce-4a43-8736-58f8ef4ab529" }),
}));
vi.mock("./GameWorld.jsx", () => ({
  default: ({ onNearBuilding, onInteract }) => (
    <div>
      <button onClick={() => onNearBuilding({ id: "science", name: "Science" })}>Approach Science</button>
      <button onClick={onInteract}>Enter nearby room</button>
    </div>
  ),
}));
vi.mock("./LearningRoomWorld.jsx", () => ({
  default: () => <div data-testid="mock-world">3D activity world</div>,
}));

import { api } from "./api.js";
import App from "./App.jsx";

describe("EDUPlay journey setup", () => {
  beforeEach(() => {
    api.mockReset();
    api.mockImplementation((path) => {
      if (path.startsWith("/curriculum/")) {
        return Promise.resolve({ classes: Array.from({ length: 12 }, (_, index) => index + 1), subjects: [] });
      }
      if (path === "/players/") {
        return Promise.resolve({
          player_id: "c1b503b3-d9ce-4a43-8736-58f8ef4ab529",
          display_name: "Mina",
          class: 9,
          xp: 0,
          coins: 0,
          level: 1,
        });
      }
      return Promise.resolve({ practicals: [] });
    });
  });

  it("creates the selected class profile and enters the campus", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.clear(screen.getByLabelText("STUDENT NAME"));
    await user.type(screen.getByLabelText("STUDENT NAME"), "Mina");
    await user.selectOptions(screen.getByLabelText("YOUR CLASS"), "9");
    await user.click(screen.getByRole("button", { name: /Enter the campus/ }));

    expect(await screen.findByRole("heading", { name: "A world of your own." })).toBeVisible();
    await waitFor(() => {
      expect(api).toHaveBeenCalledWith(
        "/players/",
        expect.objectContaining({
          method: "POST",
          body: expect.objectContaining({ display_name: "Mina", class: 9 }),
        }),
      );
    });
  });

  it("shows requested card content and supports dragging it to pick up and place", async () => {
    const user = userEvent.setup();
    const activity = {
      slug: "class-9-science-studio",
      title: "Science Discovery Studio",
      activity_type: "project",
      objective: "Sort cards to connect a science concept with an observation.",
      steps_count: 2,
      resources: [],
      simulation: { items: ["topic-cards"] },
    };
    const story = {
      title: "The Lost Observation",
      introduction: "A curious expedition needs your science skills.",
      background: "A bright discovery garden.",
      main_character: "You are a young explorer.",
      problem: "The observation cards are out of order.",
      mission: { title: "Restore the field notes", objectives: [{ title: "Collect the topic cards" }], final_challenge: "Explain the observation." },
      scenes: [{
        scene_id: "opening",
        name: "The discovery garden",
        description: "A friendly guide waves from the garden gate.",
        dialogues: [{ character: "Guide", text: "Can you help me sort these clues?" }],
      }],
    };
    const dragData = {};
    const dataTransfer = {
      types: [],
      setData(type, value) {
        dragData[type] = value;
        this.types.push(type);
      },
      getData: (type) => dragData[type] || "",
    };
    api.mockImplementation((path, options = {}) => {
      if (path.startsWith("/curriculum/")) {
        return Promise.resolve({ classes: Array.from({ length: 12 }, (_, index) => index + 1), subjects: [] });
      }
      if (path === "/players/") {
        return Promise.resolve({
          player_id: "c1b503b3-d9ce-4a43-8736-58f8ef4ab529",
          display_name: "Mina",
          class: 9,
          xp: 0,
          coins: 0,
          level: 1,
        });
      }
      if (path === "/rooms/9/science/") {
        return Promise.resolve({
          name: "Science Laboratory",
          room_type: "laboratory",
          chapters: [{ title: "Observations", activities: [activity] }],
        });
      }
      if (path.startsWith("/practicals/")) return Promise.resolve({ practicals: [] });
      if (path === "/activities/start/") {
        return Promise.resolve({
          activity,
          attempt_id: "3eb349a0-a17b-4d02-9d8a-7aa349a0a4e7",
          current_step: { action: "pick", item: "topic-cards", instruction: "Pick up the topic cards." },
          story,
        });
      }
      if (path.endsWith("/action/")) {
        if (options.body.action === "pick") {
          return Promise.resolve({
            status: "in_progress",
            step_index: 1,
            current_step: { action: "place", item: "topic-cards", instruction: "Place the topic cards on the workbench." },
            story_scene: {
              scene_id: "sorting",
              name: "The clue table",
              description: "The cards glow as you bring them to the workbench.",
              dialogues: [{ character: "Guide", text: "Great! Now arrange the clues." }],
            },
          });
        }
        return Promise.resolve({ status: "in_progress", step_index: 2 });
      }
      return Promise.resolve({ practicals: [] });
    });

    const { container } = render(<App />);
    await user.click(screen.getByRole("button", { name: /Enter the campus/ }));
    await user.click(screen.getByRole("button", { name: "Approach Science" }));
    await user.click(screen.getByRole("button", { name: "Enter nearby room" }));
    await user.click(await screen.findByRole("button", { name: "Start activity" }));

    expect(await screen.findByRole("dialog", { name: "The Lost Observation" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Begin mission/ }));
    expect(await screen.findByText("Can you help me sort these clues?")).toBeVisible();
    expect(await screen.findByText("REQUESTED OBJECT")).toBeVisible();
    expect(container.querySelector(".activity-object-preview")).toHaveTextContent(
      "Sort cards to connect a science concept with an observation.",
    );
    const requestedCard = screen.getByRole("button", { name: /topic cards, requested object/i });
    fireEvent.dragStart(requestedCard, { dataTransfer });
    fireEvent.drop(screen.getByTestId("mock-world").parentElement, { dataTransfer });

    expect(await screen.findByText("OBJECT IN HAND")).toBeVisible();
    expect(await screen.findByText("The cards glow as you bring them to the workbench.")).toBeVisible();
    const heldCard = screen.getByRole("button", { name: /topic cards.*drag to place/i });
    fireEvent.dragStart(heldCard, { dataTransfer });
    fireEvent.drop(document.querySelector(".activity-workbench"), { dataTransfer });

    await waitFor(() => {
      expect(api).toHaveBeenCalledWith(
        expect.stringMatching(/activity-attempts\/.*\/action\//),
        expect.objectContaining({ body: expect.objectContaining({ action: "place" }) }),
      );
    });
  });
});

export type WorkspacePlayer = {
  playerId: number;
  name: string;
  age: number;
  position: string;
  status: string;
  category: string;
  cr1: number;
  cr2: number;
  side: string | null;
  star: boolean;
  topWorld: boolean;
};

export type WorkspaceQueryResponse = {
  source: {
    mode: string;
    available: boolean;
    message: string;
    generatedAt: string;
  };
  career: {
    managerName: string;
    careerName: string;
    targetType: "club" | "selection";
    targetId: number;
    targetName: string;
  } | null;
  club: {
    clubId: number;
    name: string;
    stadiumName: string | null;
  } | null;
  squad: {
    total: number;
    starters: number;
    reserves: number;
    injured: number;
    players: WorkspacePlayer[];
  };
  stadium: {
    name: string | null;
    capacity: number | null;
    level: number | null;
    status: string | null;
    source: string;
  };
  training: {
    available: boolean;
    message: string;
  };
  staff: {
    members: Array<{
      staffId: number;
      name: string;
      role: string;
      age: number;
      experience: number;
      reputation: number;
      level: number;
      specialization: string | null;
      status: string;
    }>;
    departments: Array<{
      department: string;
      level: number;
      capacity: number;
      efficiency: number;
    }>;
  };
  health: {
    count: number;
  };
  scouting: {
    missions: Array<Record<string, unknown>>;
    opportunities: number;
    reports: number;
  };
};

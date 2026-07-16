import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getProjects,
  getProjectById,
  createProject,
  updateProject,
  deleteProject,
} from '../api/projects'

function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: getProjects })
}

function useProject(id) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => getProjectById(id),
    enabled: Boolean(id),
  })
}

function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

function useUpdateProject(id) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => updateProject(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', id] })
    },
  })
}

function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export { useProjects, useProject, useCreateProject, useUpdateProject, useDeleteProject }

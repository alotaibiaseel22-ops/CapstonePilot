import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  getProjects,
  getProjectById,
  createProject,
  updateProject,
  deleteProject,
} from '../api/projects'

function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: ({ signal }) => getProjects(signal),
  })
}

function useProject(id) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: ({ signal }) => getProjectById(id, signal),
    enabled: Boolean(id),
  })
}

function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project created')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not create the project.')
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
      toast.success('Project updated')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not update the project.')
    },
  })
}

function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project deleted')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not delete the project.')
    },
  })
}

export { useProjects, useProject, useCreateProject, useUpdateProject, useDeleteProject }
